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

## Pre and post scripts

Imagine you want to back up a PostgreSQL server. You could run the image with
this `docker-compose.yaml`:

```yaml
version: "2"
services:
    db:
        image: postgres
        environment:
            POSTGRES_DB: example
    backup:
        image: tecnativa/duplicity
        environment:
            PGHOST: db
            SRC: file:///mnt/postgres
            DST: s3://example.com/backup/postgres
            JOB_80_WHAT: mkdir -p /mnt/postgres
            JOB_80_WHEN: daily
            JOB_100_WHAT: pg_dump example > /mnt/postgres/example.sql
            JOB_100_WHEN: daily
```

This example by itself will probably not work, but you get the point.

[PostgreSQL][] and [MariaDB][] client tools come included. Additional DB
clients can be added if you need them.

## Using Duplicity

Refer to [Duplicity man page](http://duplicity.nongnu.org/duplicity.1.html), or
execute:

    docker run -it --rm tecnativa/duplicity duplicity --help


[Alpine]: https://alpinelinux.org/
[Duplicity]: http://duplicity.nongnu.org/
[env]: http://duplicity.nongnu.org/duplicity.1.html#sect6
[options]: http://duplicity.nongnu.org/duplicity.1.html#sect5
[PostgreSQL]: https://www.postgresql.org/
[MariaDB]: https://mariadb.org/
