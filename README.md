[![Last image-template](https://img.shields.io/badge/last%20template%20update-v0.1.3-informational)](https://github.com/Tecnativa/image-template/tree/v0.1.3)
[![GitHub Container Registry](https://img.shields.io/badge/GitHub%20Container%20Registry-latest-%2324292e)](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity)

# Duplicity Cron Runner

<details>
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<summary>Table of contents</summary>

- [What?](#what)
- [Why?](#why)
- [How?](#how)
- [Where?](#where)
- [Available images](#available-images)
- [Tags](#tags)
- [Environment variables available](#environment-variables-available)
  - [`CRONTAB_{15MIN,HOURLY,DAILY,WEEKLY,MONTHLY}`](#crontab_15minhourlydailyweeklymonthly)
  - [`DBS_TO_{INCLUDE,EXCLUDE}`](#dbs_to_includeexclude)
  - [`DST`](#dst)
  - [`EMAIL_FROM`](#email_from)
  - [`EMAIL_SUBJECT`](#email_subject)
  - [`EMAIL_TO`](#email_to)
  - [`JOB_*_WHAT`](#job__what)
  - [`JOB_*_WHEN`](#job__when)
  - [`JOB_*_HEALTHCHECKS_URL`](#job__healthchecks_url)
  - [`JOB_*_UPTIME_KUMA_URL`](#job__uptime_kuma_url)
  - [`OPTIONS`](#options)
  - [`OPTIONS_EXTRA`](#options_extra)
  - [`SMTP_HOST`](#smtp_host)
  - [`SMTP_PORT`](#smtp_port)
  - [`SMTP_USER`](#smtp_user)
  - [`SMTP_PASS`](#smtp_pass)
  - [`SMTP_TLS`](#smtp_tls)
  - [`SMTP_REPORT_SUCCESS`](#smtp_report_success)
  - [`SRC`](#src)
  - [`TZ`](#tz)
- [Set a custom hostname!](#set-a-custom-hostname)
- [Pre and post scripts](#pre-and-post-scripts)
- [Using Duplicity](#using-duplicity)
  - [Shortcuts](#shortcuts)
- [Testing your configuration](#testing-your-configuration)
- [Prebuilt flavors](#prebuilt-flavors)
  - [Normal (`docker-duplicity`)](#normal-docker-duplicity)
  - [PostgreSQL (`docker-duplicity-postgres`)](#postgresql-docker-duplicity-postgres)
  - [Docker (`docker-duplicity-docker`)](#docker-docker-duplicity-docker)
  - [Amazon S3 (`*-s3`)](#amazon-s3--s3)
  - [Multi (`*-multi`)](#multi--multi)
- [Development](#development)
  - [Testing](#testing)
  - [Managing packages](#managing-packages)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
</details>

## What?

This image includes [Duplicity][] ready to make backups of whatever you need,
cron-based.

## Why?

Because you need to back things up regularly, and Duplicity is one of the best tools
available for such a purpose.

## How?

Installing every possible Duplicity dependency to support all of its backends inside an
[Alpine][] system that is very lightweight by itself, and a little job runner Python
script that takes care of converting some environment variables into flexible cron jobs
and sending an email report automatically.

## Where?

- [Source code](https://github.com/Tecnativa/docker-duplicity).
- [Prebuilt images in GitHub package registry](https://github.com/Tecnativa/docker-duplicity/packages/).

## Available images

Each of the built-in [flavors][flavors] is separated into a specific docker image:

- [`docker-duplicity`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity)
- [`docker-duplicity-s3`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity-s3)
- [`docker-duplicity-docker`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity-docker)
- [`docker-duplicity-docker-s3`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity-docker-s3)
- [`docker-duplicity-postgres`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity-postgres)
- [`docker-duplicity-postgres-s3`](https://github.com/orgs/Tecnativa/packages/container/package/docker-duplicity-postgres-s3)

Check the [section bellow][flavors] to get more info.

## Tags

Each of the images mentioned above are tagged with `:latest`, referring to the latest
_tagged_ version in git, and `:egde`, referring to the latest version in the `master`
branch. Each individual git released version is also tagged (e.g. `:0.1.0`)

## Environment variables available

Apart from the [environment variables that Duplicity uses by default][env], you have
others specific for this image.

### `CRONTAB_{15MIN,HOURLY,DAILY,WEEKLY,MONTHLY}`

Define the cron schedule to run jobs under such circumstances.

Possibly non-obvious [defaults][dockerfile]:

- Daily: 2 AM, from Monday to Saturday
- Weekly: 1 AM, on Sundays
- Monthly: 5 AM, 1st day of month

Hours are expressed in UTC.

**If you define any of these variables wrongly, your cron might not work!**

You can use online tools such as https://crontab.guru to make it easy.

If you set these values in `.env` file, don't use quotes:

```
CRONTAB_15MIN=*/15 * * * *
CRONTAB_HOURLY=0 * * * *
CRONTAB_DAILY=0 2 * * MON-SAT
CRONTAB_WEEKLY=0 1 * * SUN
CRONTAB_MONTHLY=0 5 1 * *
```

### `DBS_TO_{INCLUDE,EXCLUDE}`

Only available in the [PostgreSQL flavors](#postgresql-docker-duplicity-postgres).

Define a Regular Expression to filter databases that shouldn't be included in the DB
dump.

You can use this to avoid getting permission errors when running a backup against a
server where you don't control all the databases.

For example, if you don't want to include the databases named `DB1` and `DB2` you can
use:

```bash
DBS_TO_EXCLUDE="^(DB1|DB2)$"
```

Or, if you only want to include those databases that start with `prod`:

```sh
DBS_TO_INCLUDE="^prod"
```

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
- `{hostname}` will be the container's host name, including the domainname (a.k.a.
  FQDN).

This variable is optional; the default is
`Backup report: {hostname} - {periodicity} - {result}`

### `EMAIL_TO`

Email report recipient. Multiple recipients can be defined as a comma-separated list of
emails.

### `JOB_*_WHAT`

Define a command that needs to be executed.

Check the `Dockerfile` to see built-in jobs.

### `JOB_*_WHEN`

Define when to execute the command you defined in the previous section. If you need
several values, you can separate them with spaces (example: `daily monthly`).

[Prebuilt flavors][flavors] provide built-in jobs. You can disable those jobs by setting
corresponding `JOB_*_WHEN` to value `never`.

### `JOB_*_HEALTHCHECKS_URL`

[healthchecks](https://healthchecks.io/) URL to ping on job success or failure. Supports
"start", "success", and "failure" pings. For a job that runs with multiple
periodicities, the periodicity can be added to the env var (e.g.
`JOB_200_DAILY_HEALTHCHECKS_URL` or `JOB_200_WEEKLY_HEALTHCHECKS_URL`) to specify
different URLs for each run. Periodicity-specific env vars take precedence over the
general one.

### `JOB_*_UPTIME_KUMA_URL`

[uptime-kuma](https://github.com/louislam/uptime-kuma) push monitor URL to ping on job
success or failure. Supports "up" and "down" pings. Do not include any query parameters
in the URL. For a job that runs with multiple periodicities, the periodicity can be
added to the env var (e.g. `JOB_200_DAILY_UPTIME_KUMA_URL` or
`JOB_200_WEEKLY_UPTIME_KUMA_URL`) to specify different URLs for each run.
Periodicity-specific env vars take precedence over the general one.

### `OPTIONS`

String to let you define [options for duplicity][options].

### `OPTIONS_EXTRA`

String that some [prebuilt flavors][flavors] use to add custom options required for that
flavor. You should never need to use this variable.

### `SMTP_HOST`

Host used to send the email report.

### `SMTP_PORT`

Port used to send the email report.

### `SMTP_USER`

If your mail server requires authentication, specify the user account to log in.

### `SMTP_PASS`

If your mail server requires authentication, specify the password for the SMTP_USER.

### `SMTP_TLS`

Force the email client to connect to the server using SLL/TLS. Note that the client will
utilize STARTTLS, regardless of this variable, if the server offers STARTTLS.

### `SMTP_REPORT_SUCCESS`

If enabled, report via SMTP regardless of exit status (this is the default behaviour).
Otherwise, only report if one or more jobs failed.

### `SRC`

What to back up.

Example: `file:///mnt/my_files`

By default, SRC is set to /mnt/backup/src/ inside the container. Simply mount any
external directory as a volume to /mnt/backup/src/. If you wish to include multiple
directories, mount them as subdirectories of /mnt/backup/src/, like...

```yaml
volumes:
  - /path/to/data/to/backup1:/mnt/backup/src/foldername1:ro
  - /path/to/data/to/backup2:/mnt/backup/src/foldername2:ro
```

### `TZ`

Define a valid timezone (i.e. `Europe/Madrid` or `America/New_York`) to make log hours
match your local reality.

This is achieved directly by bundling [the `tzdata` package][tzdata]. Refer to its docs
for more info.

## Set a custom hostname!

Duplicity checks the host name that it backs up and aborts the process if it detects a
mismatch by default.

Docker uses volatile host names, so you better add `--hostname` (and maybe also
`--domainname`) when running this container to make profit of this feature, or add
`--allow-source-mismatch` to `OPTIONS` environment variable. Otherwise, you will get
errors like:

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

Refer to [Duplicity man page](https://duplicity.readthedocs.io/en/latest/), or execute:

    docker run -it --rm ghcr.io/tecnativa/docker-duplicity duplicity --help

### Shortcuts

You can use these bundled binaries to work faster:

- `dup`: Executes duplicity prefixed with the options defined in `$OPTIONS` and
  `$OPTIONS_EXTRA` (see above).
- `backup`: Executes an immediate backup with default options.
- `restore`: Restores immediately with default options. Most likely, you will need to
  use it with `--force`.
- `/etc/periodic/daily/jobrunner`: execute immediately all jobs scheduled for daily
  backups. Change `daily` for other periodicity if you want to run those instead.

## Testing your configuration

If you want to test how do your `daily` jobs work, just run:

    docker exec -it your_backup_container /etc/periodic/daily/jobrunner

Replace `daily` by any other periodicity to test it too.

## Prebuilt flavors

Sometimes you need more than just copying a file here, pasting it there. That's why we
supply some special flavours of this image.

### Normal (`docker-duplicity`)

This includes just the most basic packages to boot the cron and use Duplicity with any
backend. All other images are built on top of this one, so downloading several flavours
won't repeat the abse layers (disk-friendly!).

It's [preconfigured][dockerfile] to backup daily:

```
# Incremental backup of all files
JOB_300_WHEN=daily
```

### PostgreSQL (`docker-duplicity-postgres`)

If you want to back up a PostgreSQL server, make sure you run this image in a fashion
similar to this `docker-compose.yaml` definition:

```yaml
services:
  db:
    image: postgres:9.6-alpine
    environment:
      POSTGRES_PASSWORD: mypass
      POSTGRES_USER: myuser
      POSTGRES_DB: mydb
  backup:
    image: ghcr.io/tecnativa/docker-duplicity-postgres
    hostname: my.postgres.backup
    environment:
      # Postgres connection
      PGHOST: db # This is the default
      PGPASSWORD: mypass
      PGUSER: myuser

      # Additional configurations for Duplicity
      AWS_ACCESS_KEY_ID: example amazon s3 access key
      AWS_SECRET_ACCESS_KEY: example amazon s3 secret key
      DST: boto3+s3://mybucket/myfolder
      EMAIL_FROM: backup@example.com
      EMAIL_TO: alerts@example.com
      OPTIONS: --s3-european-buckets --s3-use-new-style
      PASSPHRASE: example backkup encryption secret
```

It will make [dumps automatically][dockerfile]:

```
# Makes postgres dumps for all databases except to templates and "postgres".
# They are uploaded by JOB_300_WHEN
JOB_200_WHEN=daily weekly
```

### Docker (`docker-duplicity-docker`)

Imagine you need to run some command in another container to generate a backup file
before actually backing it up in a remote place.

If this is your case, you can use this version, which includes a prepackaged Docker
client.

See this `docker-compose.yaml` example, where we back up a Gitlab server using its
[crappy official image][gitlab-ce]:

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
    image: ghcr.io/tecnativa/docker-duplicity-docker
    hostname: backup
    domainname: gitlab.example.com
    privileged: true # To speak with host's docker socket
    volumes:
      - config:/mnt/backup/src/config
      - data:/mnt/backup/src/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      # Generate Gitlab backup before uploading it
      JOB_200_WHAT: docker exec projectname_gitlab_1 gitlab-rake gitlab:backup:create
      JOB_200_WHEN: daily weekly

      # Additional configurations for Duplicity
      AWS_ACCESS_KEY_ID: example amazon s3 access key
      AWS_SECRET_ACCESS_KEY: example amazon s3 secret key
      DST: boto3+s3://mybucket/myfolder
      EMAIL_FROM: backup@example.com
      EMAIL_TO: alerts@example.com
      OPTIONS: --s3-european-buckets --s3-use-new-style
      PASSPHRASE: example backup encryption secret
```

### Amazon S3 (`*-s3`)

Any of the other flavors has a special variant suffixed with `-s3`. It provides some
opinionated defaults to make good use of S3 different storage types and its lifecycle
rules and filters, assuming you want to have [weekly full backups][dockerfile]. You
should combine it with lifecycle and expiration rules at your will.

```
# Full backup of all files
JOB_500_WHEN=weekly
```

Note, that for `DST` variable you should use `boto3+s3://bucket_name[/prefix]` style.

### Multi (`*-multi`)

At the moment only "postgres" has this flavor. It extends from 'postgres-s3' and
provides some defaults to make good use of "DST\_{N}" env. variables. and uses the extra
options according to destination.

In this mode the `$DST` is set to `multi`. This enables the use of `$DST_{N}` and
`$DST_{N}_{ENV_VAR_NAME}`.

`$DST_{N}_{ENV_VAR_NAME}` will be process as `${ENV_VAR_NAME}`.

For example:

```yaml
  backup:
    ...
    environment:
      ...
      DST_1: scp://uid@other.host//usr/backup
      DST_2: boto3+s3://mybucket/myfolder
      DST_2_AWS_ACCESS_KEY_ID: example amazon s3 access key
      DST_2_AWS_SECRET_ACCESS_KEY: example amazon s3 secret key
      DST_3: rsync://user@192.168.0.54:8022//volume1/folder/
      DST_3_RSYNC_PASSWORD: the password to use with rsync
```

The `restore` process uses the first destination defined.

[alpine]: https://alpinelinux.org/
[dockerfile]: https://github.com/Tecnativa/docker-duplicity/blob/master/Dockerfile
[duplicity]: https://duplicity.gitlab.io
[flavors]: #prebuilt-flavors
[gitlab-ce]: https://hub.docker.com/r/gitlab/gitlab-ce/
[mariadb]: https://mariadb.org/
[odoobase]: https://hub.docker.com/r/tecnativa/odoo-base/builds/
[options]: https://gitlab.com/duplicity/duplicity
[postgresql]: https://www.postgresql.org/
[tzdata]: https://pkgs.alpinelinux.org/package/edge/main/aarch64/tzdata

## Development

All the dependencies you need to develop this project (apart from Docker itself) are
managed with [poetry](https://python-poetry.org/).

To set up your development environment, run:

```bash
pip install pipx  # If you don't have pipx installed
pipx install poetry  # Install poetry itself
poetry install  # Install the python dependencies and setup the development environment
```

### Testing

To run the tests locally, add `--prebuild` to autobuild the image before testing:

```sh
poetry run pytest --prebuild
```

By default, the image that the tests use (and optionally prebuild) is named
`test:docker-duplicity`. If you prefer, you can build it separately before testing, and
remove the `--prebuild` flag, to run the tests with that image you built:

```sh
docker image build -t test:docker-duplicity .
poetry run pytest
```

If you want to use a different image, pass the `--image` command line argument with the
name you want:

```sh
# To build it automatically
poetry run pytest --prebuild --image my_custom_image

# To prebuild it separately
docker image build -t my_custom_image .
poetry run pytest --image my_custom_image
```

### Managing packages

The poetry project configuration (in the `pyproject.toml` file) includes a section which
contains the duplicity dependencies themselves. This allows us to manage those more
easily and avoid future conflicts. Those are then exported into a `requirements.txt`
file in the docker image build phase.

So, if you need to add a new duplicity dependency to be used inside the container, the
correct process would be:

1. Add the dependency to the poetry project with:

   ```bash
   poetry add --optional MY_NEW_PACKAGE
   ```

   Note that it should be marked as an **optional** dependency, as it will not be used
   in general development _outside_ the container.

1. The new optional dependency should then be added to the duplicity list in the
   `[tool.poetry.extras]` section of `pyproject.toml`

   ```toml
   [tool.poetry.extras]
   duplicity = ["b2", "b2sdk", "boto", "boto3", "gdata", "jottalib", "paramiko", "pexpect", "PyDrive", "pyrax", "python", "requests", "duplicity", "dropbox", "python", "mediafire", "MY_NEW_PACKAGE"]
   ```
