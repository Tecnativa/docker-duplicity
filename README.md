# Duplicity

[Duplicity](http://duplicity.nongnu.org/) with support for all of its backends.

## Entrypoint

This image includes an entrypoint, so you only have to pass in the arguments
for `duplicity`, not the `duplicity` command. E.g.:

    docker run -it tecnativa/duplicity /home/me sftp://uid@example.com/some_dir

## Cron mode

If you set the environment variable `$LOOP_SECONDS` to any integer, `duplicity`
command will run on container start and after that amount of seconds, with
the same options. E.g. to run each 24h:

    docker run -it -e LOOP_SECONDS=86400 tecnativa/duplicity /home/me sftp://uid@example.com/some_dir

This is very useful if you want to use it along with some other containers,
because you can mount volumes from those and then keep the backup service
running. E.g. with docker-compose:

    version: "2"
    services:
        redis:
            image: redis  # Defines a /data volume

        duplicity:
            volumes_from:
                - redis
            environment:
                LOOP_SECONDS: 86400
            command: /data sftp://uid@example.com/some_dir

## Using Duplicity

Refer to [Duplicity man page](http://duplicity.nongnu.org/duplicity.1.html), or
execute:

    docker run -it --rm tecnativa/duplicity --help
