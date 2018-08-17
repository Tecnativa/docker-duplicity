FROM index.docker.io/tecnativa/duplicity
RUN apk add --no-cache postgresql
ENV JOB_200_WHAT='pg_dump --no-owner --file "$SRC/$PGDATABASE.sql"' \
    JOB_200_WHEN='daily weekly' \
    PGHOST=db
