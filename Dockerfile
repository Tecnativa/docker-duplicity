FROM python:3.13.7-slim AS builder

WORKDIR /app
ADD pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==2.0.1
RUN poetry self add poetry-plugin-export

# Build a requirements.txt file matching poetry.lock, that pip understands
# Test comment
RUN poetry export --extras duplicity --output /app/requirements.txt

FROM python:3.13.7-alpine AS base

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
    SMTP_PORT='25' \
    SMTP_USER='' \
    SMTP_PASS='' \
    SMTP_TLS='' \
    SMTP_REPORT_SUCCESS='1' \
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
        rsync \
        tzdata \
    && sync

# Default backup source directory
RUN mkdir -p "$SRC"

# Preserve cache among containers
VOLUME [ "/root" ]

# Build dependencies
COPY --from=builder /app/requirements.txt requirements.txt
RUN apk add --no-cache --virtual .build \
        build-base \
        python3-dev \
        krb5-dev \
        libffi-dev \
        librsync-dev \
        libxml2-dev \
        libxslt-dev \
        openssl-dev \
        cargo
# Trick for passing as a warning this build message and gets netifaces installed:
#    initialization of 'int' from 'void *' makes integer from pointer without a cast [-Wint-conversion]
RUN CFLAGS="-Wno-int-conversion" pip install netifaces
# Runtime dependencies, based on https://gitlab.com/duplicity/duplicity/-/blob/master/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build \
    && rm -rf /root/.cargo

COPY bin/* /usr/local/bin/
RUN chmod a+rx /usr/local/bin/* && sync

FROM base AS s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'


FROM base AS docker
RUN apk add --no-cache docker-cli


FROM docker AS docker-s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'


FROM base AS postgres

ENV DB_VERSION="latest" \
    APK_POSTGRES_DIR="/opt/postgresql-client-collection"

RUN apk add --no-cache grep libpq postgresql-common

# To get support for psql 9.6 need create the folder for 9.6, use alpine 3.6 and use these lines:
# echo "http://dl-cdn.alpinelinux.org/alpine/v3.6/main" > psql_repos
# apk fetch --no-cache --repositories-file psql_repos postgresql-client postgresql-dev -o "$APK_POSTGRES_DIR/9.6"
RUN set -eux; \
    mkdir -p \
        "$APK_POSTGRES_DIR/10" \
        "$APK_POSTGRES_DIR/11" \
        "$APK_POSTGRES_DIR/12" \
        "$APK_POSTGRES_DIR/13" \
        "$APK_POSTGRES_DIR/14" \
        "$APK_POSTGRES_DIR/15" \
        "$APK_POSTGRES_DIR/16" \
        "$APK_POSTGRES_DIR/17" \
        "$APK_POSTGRES_DIR/latest"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.8/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql-client -o "$APK_POSTGRES_DIR/10"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.10/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql-client -o "$APK_POSTGRES_DIR/11"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.12/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql-client -o "$APK_POSTGRES_DIR/12"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.14/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql-client -o "$APK_POSTGRES_DIR/13"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.17/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql14-client -o "$APK_POSTGRES_DIR/14"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.20/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql15-client -o "$APK_POSTGRES_DIR/15"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql16-client -o "$APK_POSTGRES_DIR/16"; \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.22/main" > psql_repos; \
    apk fetch --no-cache --repositories-file psql_repos postgresql17-client -o "$APK_POSTGRES_DIR/17"; \
    apk fetch --no-cache postgresql-client -o "$APK_POSTGRES_DIR/latest"; \
    rm psql_repos;

ENV JOB_200_WHAT set -euo pipefail; psql -0Atd postgres -c \"SELECT datname FROM pg_database WHERE NOT datistemplate AND datname != \'postgres\'\" | grep --null-data -E \"\$DBS_TO_INCLUDE\" | grep --null-data --invert-match -E \"\$DBS_TO_EXCLUDE\" | xargs -0tI DB pg_dump --dbname DB --no-owner --no-privileges --file \"\$SRC/DB.sql\"
ENV JOB_200_WHEN='daily weekly' \
    DBS_TO_INCLUDE='.*' \
    DBS_TO_EXCLUDE='$^' \
    PGHOST=db


FROM postgres AS postgres-s3
ENV JOB_500_WHAT='dup full $SRC $DST' \
    JOB_500_WHEN='weekly' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)- --s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'


FROM postgres-s3 AS postgres-multi
ENV DST='multi' \
    OPTIONS_EXTRA='--metadata-sync-mode partial --full-if-older-than 1W --file-prefix-archive archive-$(hostname -f)- --file-prefix-manifest manifest-$(hostname -f)- --file-prefix-signature signature-$(hostname -f)-' \
    OPTIONS_EXTRA_S3='--s3-european-buckets --s3-multipart-chunk-size 10 --s3-use-new-style'
