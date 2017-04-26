# [Duplicity][] Cron Runner

[![](https://images.microbadger.com/badges/version/tecnativa/duplicity:latest.svg)](https://microbadger.com/images/tecnativa/duplicity:latest "Get your own version badge on microbadger.com")
[![](https://images.microbadger.com/badges/image/tecnativa/duplicity:latest.svg)](https://microbadger.com/images/tecnativa/duplicity:latest "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/commit/tecnativa/duplicity:latest.svg)](https://microbadger.com/images/tecnativa/duplicity:latest "Get your own commit badge on microbadger.com")
[![](https://images.microbadger.com/badges/license/tecnativa/duplicity.svg)](https://microbadger.com/images/tecnativa/duplicity "Get your own license badge on microbadger.com")

## What?

This image includes Duplicity ready to make backups of whatever you need,
cron-based.

## Why?

Because you need to back things up regularly, and Duplicity is one of the
best tools available for such a purpose.

## How?

Installing every possible Duplicity dependency to support all of its backends
inside an [Alpine][] system that is very lightweight by itself, and a little
job runner Python script that takes care of converting some environment
variables into flexible cron jobs and sending an email report automatically.

## Environment variables available

Apart from the [environment variables that Duplicity uses by default][env], you
have others specific for this image.

### `DST`

Where to store the backup.

Example: `ftps://user@example.com/some_dir`

### `EMAIL_FROM`

Email report sender.

### `EMAIL_SUBJECT`

Subject of the email report. You can use these placeholders:

- `{periodicity}` will be one of these:
  - `15min`
  - `hourly`
  - `daily`
  - `weekly`
  - `monthly`
- `{result}` will be:
  - `OK` if all worked fine.
  - `ERROR` if any job failed.
- `{hostname}` will be the container's host name, which you should explicitly
  set.

### `EMAIL_TO`

Email report recipient.

### `JOB_*_WHAT`

Define a command that needs to be executed.

Built-in jobs:

- `JOB_300_WHAT`: `duplicity $OPTIONS $SRC $DST`
- `JOB_600_WHAT`: `duplicity full $OPTIONS $SRC $DST`

### `JOB_*_WHEN`

Define when to execute the command you defined in the previous section. If you
need several values, you can separate them with spaces (example: `daily
monthly`).

Built-in jobs:

- `JOB_300_WHEN`: `daily`
- `JOB_600_WHEN`: `weekly`

### `OPTIONS`

String to let you define [options for duplicity][options].

### `SMTP_HOST`

Host used to send the email report.

### `SMTP_PORT`

Port used to send the email report.

### `SRC`

What to back up.

Example: `file:///mnt/my_files`

## Set a custom hostname!

Duplicity checks the host name that it backs up and aborts the process if it
detects a mismatch by default.

Docker uses volatile host names, so you better add `--hostname` when running
this container to make profit of this feature, or add `--allow-source-mismatch`
to `OPTIONS` environment variable. Otherwise, you will get errors like:

    Fatal Error: Backup source host has changed.
    Current hostname: 414e54ed20fb
    Previous hostname: 6529bba0969c

    Aborting because you may have accidentally tried to backup two different
    data sets to the same remote location, or using the same archive directory.
    If this is not a mistake, use the --allow-source-mismatch switch to avoid
    seeing this message

## Pre and post scripts

Add jobs through environment variable pairs. The order will be followed.

## Using Duplicity

Refer to [Duplicity man page](http://duplicity.nongnu.org/duplicity.1.html), or
execute:

    docker run -it --rm tecnativa/duplicity duplicity --help

## Prebuilt configurations

### PostgreSQL

If you want to back up a PostgreSQL server, make sure you run this image in a
fashion similar to this `docker-compose.yaml` definition:

```yaml
services:
    db:
        image: postgres:9.6-alpine
        environment:
            POSTGRES_PASSWORD: mypass
            POSTGRES_USER: myuser
            POSTGRES_DB: mydb
    backup:
        image: tecnativa/duplicity:postgres
        hostname: my.postgres.backup
        environment:
            # Postgres connection
            PGDATABASE: mydb
            PGHOST: db  # This is the default
            PGPASSWORD: mypass
            PGUSER: myuser

            # Additional configurations for Duplicity
            AWS_ACCESS_KEY_ID: example amazon s3 access key
            AWS_SECRET_ACCESS_KEY: example amazon s3 secret key
            DST: s3://s3.amazonaws.com/mybucket/myfolder
            EMAIL_FROM: backup@example.com
            EMAIL_TO: alerts@example.com
            OPTIONS: --s3-european-buckets --s3-use-new-style
            PASSPHRASE: example backkup encryption secret
```

[Alpine]: https://alpinelinux.org/
[Duplicity]: http://duplicity.nongnu.org/
[env]: http://duplicity.nongnu.org/duplicity.1.html#sect6
[MariaDB]: https://mariadb.org/
[odoobase]: https://hub.docker.com/r/tecnativa/odoo-base/builds/
[options]: http://duplicity.nongnu.org/duplicity.1.html#sect5
[PostgreSQL]: https://www.postgresql.org/
