FROM    ubuntu:18.04

RUN apt-get -y update   \
&&  apt-get -y upgrade  \
&&  apt-get -y install \
    locales \
    curl \
    git \
    vim \
    wget \
    unzip \
    openssh-server \
    sudo \
    python3 \
&&  useradd -m epoch \
&&  echo "epoch:epoch" | chpasswd \
&&  echo "epoch ALL=NOPASSWD: ALL" >> /etc/sudoers \
&&  mkdir /run/sshd

CMD ["/usr/sbin/sshd", "-De"]



