import re

import pytest
from plumbum.cmd import docker

from .conftest import MIN_PG


def test_containers_start(container_factory):
    for tag in ["docker-s3", "postgres-s3", "docker", "postgres", "s3", "base"]:
        with container_factory(tag) as test_container:
            docker(
                "exec",
                test_container,
                "dup",
                "--version",
            )


def test_docker_bin(container_factory):
    for tag in ["docker-s3", "docker"]:
        with container_factory(tag) as test_container:
            docker(
                "exec",
                test_container,
                "docker",
                "--version",
            )


def test_postgres_bin(container_factory):
    for tag in ["postgres-s3", "postgres"]:
        with container_factory(tag) as test_container:
            for app in ("psql", "pg_dump"):
                binary_name, product, version = docker(
                    "exec",
                    test_container,
                    app,
                    "--version",
                ).split()
                assert binary_name == app
                assert product == "(PostgreSQL)"
                assert float(version) >= MIN_PG


@pytest.mark.parametrize("tag", ("postgres-s3", "postgres"))
@pytest.mark.parametrize(
    "dbs_to_include, dbs_to_exclude, dbs_matched",
    (
        (None, "^demo", ["prod1", "prod2"]),
        ("^prod", None, ["prod1", "prod2"]),
        ("prod", "2", ["prod1"]),
    ),
)
def test_postgres_db_filters(
    container_factory,
    tag: str,
    postgres_container,
    dbs_to_include: str,
    dbs_to_exclude: str,
    dbs_matched: list,
):
    # Create some DBs to test
    existing_dbs = ["prod1", "prod2", "demo1", "demo2"]
    with container_factory(tag) as duplicity_container:
        # Build docker exec command
        exc = docker[
            "exec",
            "--env=PGUSER=postgres",
            "--env=PGPASSWORD=password",
            "--env=PASSPHRASE=good",
            f"--env=PGHOST={postgres_container['NetworkSettings']['IPAddress']}",
            "--env=DST=file:///mnt/backup/dst",
        ]
        if dbs_to_include is not None:
            exc = exc[f"--env=DBS_TO_INCLUDE={dbs_to_include}"]
        if dbs_to_exclude is not None:
            exc = exc[f"--env=DBS_TO_EXCLUDE={dbs_to_exclude}"]
        exc = exc[duplicity_container]
        # Create all those test dbs
        list(map(exc["createdb"], existing_dbs))
        # Back up
        exc("/etc/periodic/daily/jobrunner", retcode=None)
        # Check backup files. Output looks like this:
        #   Local and Remote metadata are synchronized, no sync needed.
        #   Last full backup date: Fri Oct 29 12:29:35 2021
        #   Fri Oct 29 12:29:34 2021 .
        #   Fri Oct 29 12:29:34 2021 demo1.sql
        #   Fri Oct 29 12:29:34 2021 demo2.sql
        output = exc("dup", "list-current-files", "file:///mnt/backup/dst")
        # Assert we backed up the correct DBs
        backed = re.findall(r" (\w+)\.sql", output)
        assert backed == dbs_matched
