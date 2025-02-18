#   Copyright 2019 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import cgi # CGIモジュールのインポート
import cgitb
import sys
import requests
import json
import subprocess
import traceback
import os
import base64
import bcrypt
import datetime, pytz
import logging

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.http.response import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from kubernetes import client, config

logger = logging.getLogger('apilog')
exec_detail = ""

@csrf_exempt
def index(request):

    logger.debug ("CALL argocd.pod : {}".format(request.method))

    if request.method == 'POST':
        return post(request)
    else:
        return ""

@csrf_exempt    
def post(request):
    try:
        exec_detail = ""

        v1 = client.CoreV1Api()
        
        logger.debug("argocd pod create")

        resource_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/resource"

        # namespace定義
        name = "epoch-workspace"

        # namespaceの存在チェック
        ret = getNamespace(name)
        if ret is None:
            # namespaceの作成
            ret = createNamespace(name)
        
        # namespaceの作成に失敗した場合
        if ret is None:
            response = {
                "result":"ERROR",
                "returncode": "0",
                "command": "createNamespace",
                "errorDetail": exec_detail,
                "output": "",
                "traceback": "",
            }
            return JsonResponse(response)

        output = ""

        logger.debug("argocd pod kubectl apply")
        # argocd pod create
        stdout_cd = subprocess.check_output(["kubectl","apply","-n",name,"-f",(resource_dir + "/argocd_install_v2_1_1.yaml")],stderr=subprocess.STDOUT)

        output += "argocd" + "{" + stdout_cd.decode('utf-8') + "},"

        logger.debug("argocd pod output:" + output)

        logger.debug("argocd nodeport kubectl apply")
        # argocd nodeport patch
        stdout_cd = subprocess.check_output(["kubectl","apply","-n",name,"-f",(resource_dir + "/argocd_nodeport.yaml")],stderr=subprocess.STDOUT)

        output += "argocd nodeport" + "{" + stdout_cd.decode('utf-8') + "},"

        logger.debug("argocd nodeport output:" + output)

        # 対象となるdeploymentを定義
        deployments = [ "deployment/argocd-server",
                        "deployment/argocd-dex-server",
                        "deployment/argocd-redis",
                        "deployment/argocd-repo-server" ]

        envs = [ "HTTP_PROXY=" + os.environ['EPOCH_HTTP_PROXY'],
                 "HTTPS_PROXY=" + os.environ['EPOCH_HTTPS_PROXY'],
                 "http_proxy=" + os.environ['EPOCH_HTTP_PROXY'],
                 "https_proxy=" + os.environ['EPOCH_HTTPS_PROXY'],
                 "NO_PROXY=" + os.environ['EPOCH_ARGOCD_NO_PROXY'],
                 "no_proxy=" + os.environ['EPOCH_ARGOCD_NO_PROXY'] ]

        logger.debug("argocd kubectl set env start")
        exec_detail = "環境変数[PROXY]を確認してください"
        for deployment_name in deployments:
            for env_name in envs:
                # 環境変数の設定
                stdout_cd = subprocess.check_output(["kubectl","set","env",deployment_name,"-n",name,env_name],stderr=subprocess.STDOUT)

                output += deployment_name + "." + env_name + "{" + stdout_cd.decode('utf-8') + "},"
        exec_detail = ""
        logger.debug("argocd kubectl set env complete")

        logger.debug("argocd rolesetting kubectl apply")
        # role bindingの再設定 (ns:epoch-workspace用)
        stdout_cd = subprocess.check_output(["kubectl","apply","-n",name,"-f",(resource_dir + "/argocd_rolebinding.yaml")],stderr=subprocess.STDOUT)

        output += "argocd" + "{" + stdout_cd.decode('utf-8') + "},"

        logger.debug("argocd rolesetting complete")

        logger.debug("argocd pod password reset")

        # argo CDのパスワード初期化
        salt = bcrypt.gensalt(rounds=10, prefix=b'2a')
        password = settings.ARGO_PASSWORD.encode("ascii")
        argoLogin = bcrypt.hashpw(password, salt).decode("ascii")
        # logger.debug("argocd pod password : {}".format(argoLogin))
        # bcryptでハッシュ化した内容でargocdのパスワードを初期化する
        datenow = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%dT%H:%M:%S%z')
        pdata ='{"stringData": { "admin.password": "' + argoLogin + '", "admin.passwordMtime": "\'' + datenow + '\'" }}'
        stdout_cd = subprocess.check_output(["kubectl","-n",name,"patch","secret","argocd-secret","-p",pdata],stderr=subprocess.STDOUT)

        output += "argocd_pwchg" + "{" + stdout_cd.decode('utf-8') + "},"

        logger.debug("argocd pod password complete")

        response = {
            "result":"OK",
            "output" : [ output
                #stdout_ns.decode('utf-8'),
                #stdout_cd.decode('utf-8'),
            ],
        }
        return JsonResponse(response, status=200)

    except subprocess.CalledProcessError as e:
        logger.debug(e.output.decode('utf-8'))
        response = {
            "result":"ERROR",
            "returncode": e.returncode,
            "errorDetail": exec_detail,
            # "command": e.cmd,
            "output": e.output.decode('utf-8'),
            "traceback": traceback.format_exc(),
        }
        return JsonResponse(response, status=500)

    except Exception as e:
        response = {
            "result":"ERROR",
            "returncode": "",
            "errorDetail": exec_detail,
            "args": e.args,
            "output": e.args,
            "traceback": traceback.format_exc(),
        }
        return JsonResponse(response, status=500)


# namespaceの情報取得
# 戻り値：namespaceの情報、存在しない場合はNone
def getNamespace(name):
    try:

        config.load_incluster_config()
        # 使用するAPIの宣言
        v1 = client.CoreV1Api()
        
        # 引数の設定
        pretty = '' # str | If 'true', then the output is pretty printed. (optional)
        exact = True # bool | Should the export be exact.  Exact export maintains cluster-specific fields like 'Namespace'. Deprecated. Planned for removal in 1.18. (optional)
        export = True # bool | Should this value be exported.  Export strips fields that a user can not specify. Deprecated. Planned for removal in 1.18. (optional)

        # namespaceの情報取得
        ret = v1.read_namespace(name=name)
        logger.debug("ret: %s" % (ret))

        return ret 

    except Exception as e:
        logger.debug("Except: %s" % (e))
        return None 
      
# namespaceの作成
# 戻り値：作成時の情報、失敗時はNone
def createNamespace(name):
    try:

        config.load_incluster_config()
        # 使用するAPIの宣言
        v1 = client.CoreV1Api()
        
        # 引数の設定
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
        # api_instance = kubernetes.client.CoreV1Api(api_client)
        # body = kubernetes.client.V1Namespace() # V1Namespace | 
        #pretty = '' # str | If 'true', then the output is pretty printed. (optional)
        #dry_run = '' # str | When present, indicates that modifications should not be persisted. An invalid or unrecognized dryRun directive will result in an error response and no further processing of the request. Valid values are: - All: all dry run stages will be processed (optional)
        #field_manager = '' # str | fieldManager is a name associated with the actor or entity that is making these changes. The value must be less than or 128 characters long, and only contain printable characters, as defined by https://golang.org/pkg/unicode/#IsPrint. (optional)

        # namespaceの作成
        #ret = v1.create_namespace(body=body, pretty=pretty, dry_run=dry_run, field_manager=field_manager)
        ret = v1.create_namespace(body=body)

        logger.debug("ret: %s" % (ret))

        return ret 

    except Exception as e:
        logger.debug("Except: %s" % (e))
        return None 
      