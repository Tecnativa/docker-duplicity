FROM python:2.7
MAINTAINER Tecnativa <info@tecnativa.com>

ARG DUPLICITY_VERSION=0.7.07.1
ENV LOOP_SECONDS=

ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "/usr/local/bin/duplicity"]
COPY *.sh /usr/local/bin/

RUN apt-get update &&\
    apt-get install -y lftp libpar2-dev librsync-dev par2 rsync &&\

    pip install --no-cache-dir \
        PyDrive \
        azure-storage \
        boto \
        lockfile \
        mediafire \
        paramiko \
        pycryptopp \
        python-keystoneclient \
        python-swiftclient \
        requests \
        requests_oauthlib \
        urllib3 \
        https://code.launchpad.net/duplicity/$(echo $DUPLICITY_VERSION | sed -r 's/^([0-9]+\.[0-9]+)([0-9\.]*)$/\1/')-series/$DUPLICITY_VERSION/+download/duplicity-$DUPLICITY_VERSION.tar.gz &&\

    apt-get -y autoremove &&\
    apt-get -y remove libpar2-dev librsync-dev &&\
    apt-get clean -y &&\
    rm -rf /var/lib/apt/lists/*
