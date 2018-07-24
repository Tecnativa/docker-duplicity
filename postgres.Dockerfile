FROM index.docker.io/tecnativa/duplicity
RUN apk add --no-cache postgresql
ENV JOB_200_WHAT='pg_dump --no-owner --file "$SRC/$PGDATABASE.pgdump"' \
    JOB_200_WHEN='daily weekly' \
    JOB_700_WHAT='rm $SRC/$PGDATABASE.pgdump' \
    JOB_700_WHEN='daily weekly' \
    PGHOST=db
