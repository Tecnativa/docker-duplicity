FROM python:3-alpine AS latest

ENV CRONTAB_15MIN='*/15 * * * *' \
    CRONTAB_HOURLY='0 * * * *' \
    CRONTAB_DAILY='0 2 * * MON-SAT' \
    CRONTAB_WEEKLY='0 1 * * SUN' \
    CRONTAB_MONTHLY='0 5 1 * *' \
    DST='' \
    EMAIL_FROM='' \
    EMAIL_SUBJECT='Backup report: {hostname} - {periodicity} - {result}' \
    EMAIL_TO='' \
    JOB_300_WHAT='backup' \
    JOB_300_WHEN='daily' \
    OPTIONS='' \
    OPTIONS_EXTRA='--metadata-sync-mode partial' \
    SMTP_HOST='smtp' \
    SMTP_PASS='' \
    SMTP_PORT='25' \
    SMTP_TLS='' \
    SMTP_USER='' \
    SRC='/mnt/backup/src'

ENTRYPOINT [ "/usr/local/bin/entrypoint" ]
CMD ["/usr/sbin/crond", "-fd8"]

# Link the job runner in all periodicities available
RUN ln -s /usr/local/bin/jobrunner /etc/periodic/15min/jobrunner
RUN ln -s /usr/local/bin/jobrunner /etc/periodic/hourly/jobrunner
RUN ln -s /usr/local/bin/jobrunner /etc/periodic/daily/jobrunner
RUN ln -s /usr/local/bin/jobrunner /etc/periodic/weekly/jobrunner
RUN ln -s /usr/local/bin/jobrunner /etc/periodic/monthly/jobrunner

# Runtime dependencies and database clients
RUN apk add --no-cache \
        ca-certificates \
        dbus \
        gettext \
        gnupg \
        krb5-libs \
        lftp \
        libffi \
        librsync \
        ncftp \
        openssh \
        openssl \
        tzdata \
    && sync

# Default backup source directory
RUN mkdir -p "$SRC"

# Preserve cache among containers
VOLUME [ "/root" ]

# Build dependencies
RUN apk add --no-cache --virtual .build \
        build-base \
        krb5-dev \
        libffi-dev \
        librsync-dev \
        libxml2-dev \
        libxslt-dev \
        openssl-dev \
    # Runtime dependencies, based on https://gitlab.com/duplicity/duplicity/-/blob/master/requirements.txt
    && pip install --no-cache-dir \
        # Backend libraries
        azure-mgmt-storage \
        b2 \
        b2sdk \
        boto \
        boto3 \
        dropbox \
        gdata \
        jottalib \
        mediafire \
        paramiko \
        pexpect \
        pydrive \
        pyrax \
        python-keystoneclient \
        python-swiftclient \
        requests_oauthlib \
        # Duplicity from source code
        https://gitlab.com/duplicity/duplicity/-/archive/rel.0.8.14/duplicity-rel.0.8.14.tar.bz2 \
    && apk del .build

COPY bin/* /usr/local/bin/
RUN chmod a+rx /usr/local/bin/* && sync

FROM latest AS latest-s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'


FROM latest AS docker
RUN apk add --no-cache docker


FROM docker AS docker-s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'


FROM latest AS postgres
RUN apk add --no-cache postgresql
ENV JOB_200_WHAT psql -0Atd postgres -c \"SELECT datname FROM pg_database WHERE NOT datistemplate AND datname != \'postgres\'\" | xargs -0tI DB pg_dump --dbname DB --no-owner --no-privileges --file \"\$SRC/DB.sql\"
ENV JOB_200_WHEN='daily weekly' \
    PGHOST=db


FROM postgres AS postgres-s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'
