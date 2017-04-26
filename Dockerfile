FROM alpine
MAINTAINER Tecnativa <info@tecnativa.com>

ARG DUPLICITY_VERSION=0.7.12

ENV DST='' \
    EMAIL_FROM='' \
    EMAIL_SUBJECT='Cron [{periodicity}] report: [{result}]' \
    EMAIL_TO='' \
    JOB_300_WHAT='duplicity incremental $OPTIONS $SRC $DST' \
    JOB_300_WHEN='daily' \
    JOB_600_WHAT='duplicity full $OPTIONS $SRC $DST' \
    JOB_600_WHEN='weekly' \
    OPTIONS='' \
    SMTP_HOST='smtp' \
    SMTP_PORT='25' \
    SRC=''

CMD ["/usr/sbin/crond", "-fd8"]

# Link the job runner in all periodicities available
RUN ln -s /usr/local/bin/jobrunner.py /etc/periodic/15min/jobrunner
RUN ln -s /usr/local/bin/jobrunner.py /etc/periodic/hourly/jobrunner
RUN ln -s /usr/local/bin/jobrunner.py /etc/periodic/daily/jobrunner
RUN ln -s /usr/local/bin/jobrunner.py /etc/periodic/weekly/jobrunner
RUN ln -s /usr/local/bin/jobrunner.py /etc/periodic/monthly/jobrunner

# Runtime dependencies and database clients
RUN apk add --no-cache \
        gnupg \
        lftp \
        libffi \
        librsync \
        mariadb-client \
        openssl \
        postgresql \
        python

# Build dependencies
RUN apk add --no-cache --virtual .build \
        build-base \
        libffi-dev \
        librsync-dev \
        linux-headers \
        openssl-dev \
        py-pip \
        python-dev \
    && pip install --no-cache-dir \
        azure-storage \
        boto \
        lockfile \
        mediafire \
        paramiko \
        pycryptopp \
        PyDrive \
        python-keystoneclient \
        python-swiftclient \
        requests \
        requests_oauthlib \
        urllib3 \
        https://code.launchpad.net/duplicity/$(echo $DUPLICITY_VERSION | sed -r 's/^([0-9]+\.[0-9]+)([0-9\.]*)$/\1/')-series/$DUPLICITY_VERSION/+download/duplicity-$DUPLICITY_VERSION.tar.gz \
    && apk del .build
COPY *.py  /usr/local/bin/
RUN chmod a+rx /usr/local/bin/*

# Metadata
ARG VCS_REF
ARG BUILD_DATE
LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.vendor=Tecnativa \
      org.label-schema.license=Apache-2.0 \
      org.label-schema.build-date="$BUILD_DATE" \
      org.label-schema.vcs-ref="$VCS_REF" \
      org.label-schema.vcs-url="https://github.com/Tecnativa/docker-duplicity"
