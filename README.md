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

Check the `Dockerfile` to see built-in jobs.

### `JOB_*_WHEN`

Define when to execute the command you defined in the previous section. If you
need several values, you can separate them with spaces (example: `daily
monthly`).

Check the `Dockerfile` to see built-in jobs.

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

## Testing your configuration

If you want to test how do your `daily` jobs work, just run:

    docker exec -it your_backup_container /etc/periodic/daily/jobrunner

Replace `daily` by any other periodicity to test it too.

## Prebuilt flavors

Sometimes you need more than just copying a file here, pasting it there. That's
why we supply some special flavours of this image.

### Normal (`latest`)

This includes just the most basic packages to boot the cron and use Duplicity
with any backend. All other images are built on top of this one, so downloading
several flavours won't repeat the abse layers (disk-friendly!).

Preconfigured to backup daily.

### PostgreSQL (`postgres`)

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

Check the `postgres.Dockerfile` file to see additional built-in jobs.

### Docker (`docker`)

Imagine you need to run some command in another container to generate a backup
file before actually backing it up in a remote place.

If this is your case, you can use this version, which includes a prepackaged
Docker client.

See this `docker-compose.yaml` example, where we back up a Gitlab server using
its [crappy official image][gitlab-ce]:

```yaml
services:
    gitlab:
        image: gitlab/gitlab-ce
        hostname: gitlab
        domainname: example.com
        environment:
            GITLAB_OMNIBUS_CONFIG: |
                # Your Gitlab configuration here
        ports:
            - "22:22"
            - "80:80"
            - "443:443"
        volumes:
            - config:/etc/gitlab:z
            - data:/var/opt/gitlab:z
            - logs:/var/log/gitlab:z
    backup:
        image: tecnativa/duplicity:docker
        hostname: backup
        domainname: gitlab.example.com
        privileged: true  # To speak with host's docker socket
        volumes:
            - config:/mnt/backup/src/config
            - data:/mnt/backup/src/data
            - /var/run/docker.sock:/var/run/docker.sock:ro
        environment:
            # Generate Gitlab backup before uploading it
            JOB_200_WHAT:
                docker exec projectname_gitlab_1
                gitlab-rake gitlab:backup:create
            JOB_200_WHEN: daily weekly

            # Additional configurations for Duplicity
            AWS_ACCESS_KEY_ID: example amazon s3 access key
            AWS_SECRET_ACCESS_KEY: example amazon s3 secret key
            DST: s3://s3.amazonaws.com/mybucket/myfolder
            EMAIL_FROM: backup@example.com
            EMAIL_TO: alerts@example.com
            OPTIONS: --s3-european-buckets --s3-use-new-style
            PASSPHRASE: example backkup encryption secret
```

### Amazon S3 (`*-s3`)

Any of the other flavors has a special variant suffixed with `-s3`. It
provides some opinionated defaults to make good use of S3 different storage
types and its lifecycle rules and filters, assuming you want to keep 3 months
of backups.

[Alpine]: https://alpinelinux.org/
[Duplicity]: http://duplicity.nongnu.org/
[env]: http://duplicity.nongnu.org/duplicity.1.html#sect6
[gitlab-ce]: https://hub.docker.com/r/gitlab/gitlab-ce/
[MariaDB]: https://mariadb.org/
[odoobase]: https://hub.docker.com/r/tecnativa/odoo-base/builds/
[options]: http://duplicity.nongnu.org/duplicity.1.html#sect5
[PostgreSQL]: https://www.postgresql.org/
