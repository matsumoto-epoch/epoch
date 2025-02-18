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
import datetime, pytz
import time
import base64
import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('apilog')

@csrf_exempt
def index(request):
    if request.method == 'POST':
        return post(request)
    else:
        return ""

@csrf_exempt    
def post(request):
    try:
        # パラメータ情報(JSON形式)
        payload = json.loads(request.body)
        
        operation_id = payload["operation_id"]
        conductor_class_no = payload["conductor_class_no"]
        preserve_datetime = payload["preserve_datetime"]
        host = os.environ['EPOCH_ITA_HOST'] + ':' + os.environ['EPOCH_ITA_PORT']
        auth = base64.b64encode((os.environ['EPOCH_ITA_USER'] + ':' + os.environ['EPOCH_ITA_PASSWORD']).encode())

        # POST送信する
        # ヘッダ情報
        header = {
            'host': host,
            'Content-Type': 'application/json',
            'Authorization': auth,
            'X-Command': 'EXECUTE',
        }

        # 実行パラメータ設定
        data = {
            "CONDUCTOR_CLASS_NO": conductor_class_no,
            "OPERATION_ID": operation_id,
            "PRESERVE_DATETIME": preserve_datetime,
        }

        logger.debug("-------------------------")
        logger.debug("header:")
        logger.debug(header)
        logger.debug("")
        logger.debug("data:")
        logger.debug(data)
        logger.debug("-------------------------")
        # json文字列に変換（"utf-8"形式に自動エンコードされる）
        json_data = json.dumps(data)

        # リクエスト送信
        exec_response = requests.post('http://' + host + '/default/menu/07_rest_api_ver1.php?no=2100180004', headers=header, data=json_data)

        logger.debug("-------------------------")
        logger.debug("response:")
        logger.debug(exec_response.text)
        logger.debug("-------------------------")

        response = {
            "result": "200",
            "output": exec_response.text,
            "datetime": datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S'),
        }
        return JsonResponse(response)

    except Exception as e:
        response = {
            "result": "500",
            "output": traceback.format_exc(),
            "datetime": datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S'),
        }
        return JsonResponse(response)
