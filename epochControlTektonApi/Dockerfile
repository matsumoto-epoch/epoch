FROM    ubuntu:18.04

RUN echo "RUN START"  \
&&  apt-get -y update   \
&&  apt-get -y upgrade  \
&&  apt-get -y install \
    locales \
    curl \
    python3-distutils \
    git \
    vim \
#    sudo \
    wget \
    unzip \
    mysql-client \
&&  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
&&  python3 get-pip.py \
&&  pip install -U pip \
&&  pip install requests \
&&  pip install kubernetes \
&&  python3 -m pip install Flask \
&&  python3 -m pip install pytz \
&&  python3 -m pip install mysql-connector-python \
&&  python3 -m pip install markdown \
&&  curl -LO -k "https://storage.googleapis.com/kubernetes-release/release/$(curl -s -k https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl" \
&&  chmod +x ./kubectl \
&&  mv ./kubectl /usr/local/bin/kubectl \
&&  curl -LO https://github.com/tektoncd/cli/releases/download/v0.18.0/tkn_0.18.0_Linux_x86_64.tar.gz \
&&  tar xvzf tkn_0.18.0_Linux_x86_64.tar.gz -C /usr/local/bin/ tkn \
&&  ln -s /usr/local/bin/tkn /usr/local/bin/kubectl-tkn \
&&  echo "RUN FINISH"

WORKDIR /app

RUN echo "RUN START"  \
&&  git clone -b main "https://github.com/exastro-suite/epoch.git"

CMD ["python3", "/app/epoch/epochControlTektonApi/api_tekton.py"]

