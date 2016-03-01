FROM python:2.7

RUN apt-get update \
    && apt-get install -y lftp librsync-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir boto lockfile paramiko pycryptopp urllib3 azure-storage requests requests_oauthlib PyDrive python-swiftclient python-keystoneclient

RUN cd /tmp \
    && wget https://code.launchpad.net/duplicity/0.7-series/0.7.06/+download/duplicity-0.7.06.tar.gz \
    && tar xf duplicity-0.7.06.tar.gz \
    && cd duplicity-0.7.06 && python2 setup.py install \
    && cd /tmp \
    && wget http://netcologne.dl.sourceforge.net/project/ftplicity/duply%20%28simple%20duplicity%29/1.11.x/duply_1.11.2.tgz \
    && tar xpf duply_1.11.2.tgz \
    && cp -a duply_1.11.2/duply /usr/bin/duply \
    && cd / && rm -rf /tmp/*

