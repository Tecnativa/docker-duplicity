import logging
import re

import pytest
from plumbum.cmd import docker

_logger = logging.getLogger(__name__)


def test_containers_start(container_factory):
    for tag in [
        "docker-s3",
        "postgres-s3",
        "postgres-multi",
        "docker",
        "postgres",
        "s3",
        "base",
    ]:
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
    for tag in ["postgres-multi", "postgres-s3", "postgres"]:
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
                assert float(version) >= pytest.MIN_PG


@pytest.mark.parametrize("tag", ("postgres-multi", "postgres-s3", "postgres"))
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


@pytest.mark.parametrize("tag", ("postgres-multi", "postgres-s3", "postgres"))
@pytest.mark.parametrize(
    "dbs_matched",
    (["prod1"],),
)
def test_postgres_restore(
    container_factory,
    tag: str,
    postgres_container,
    dbs_matched: list,
):
    with container_factory(tag) as duplicity_container:
        # Build docker exec command
        exc = docker[
            "exec",
            "--env=PGUSER=postgres",
            "--env=PGPASSWORD=password",
            "--env=PASSPHRASE=good",
            f"--env=PGHOST={postgres_container['NetworkSettings']['IPAddress']}",
            "--env=SRC=/mnt/backup/src",
            "--env=DST=file:///mnt/backup/dst",
        ]
        exc = exc[duplicity_container]
        # Create all those test dbs
        list(map(exc["createdb"], dbs_matched))
        # Backup
        exc("/etc/periodic/daily/jobrunner")
        exc("rm", "-rf", "/mnt/backup/src")
        with pytest.raises(Exception):
            output = exc("ls", "/mnt/backup/src")
        exc("restore")
        # Check restored files. Output looks like this:
        #   prod1.sql
        output = exc("ls", "/mnt/backup/src")
        backed = re.findall(r"\s?(\w+)\.sql", output)
        assert backed == dbs_matched


@pytest.mark.parametrize(
    "dbs_to_include, dbs_to_exclude, dbs_matched, dests",
    (
        (None, "^demo", ["prod1", "prod2"], ["file:///mnt/backup/dst_1"]),
        (
            "^prod",
            None,
            ["prod1", "prod2"],
            ["file:///mnt/backup/dst_1", "file:///mnt/backup/dst_2"],
        ),
        (
            "prod",
            "2",
            ["prod1"],
            [
                "file:///mnt/backup/dst_1",
                "file:///mnt/backup/dst_2",
                "file:///mnt/backup/dst_3",
            ],
        ),
    ),
)
def test_postgres_multi(
    container_factory,
    postgres_container,
    dbs_to_include: str,
    dbs_to_exclude: str,
    dbs_matched: list,
    dests: list,
):
    # Create some DBs to test
    existing_dbs = ["prod1", "prod2", "demo1", "demo2"]
    with container_factory("postgres-multi") as duplicity_container:
        # Build docker exec command
        exc = docker[
            "exec",
            "--env=PGUSER=postgres",
            "--env=PGPASSWORD=password",
            "--env=PASSPHRASE=good",
            f"--env=PGHOST={postgres_container['NetworkSettings']['IPAddress']}",
        ]
        for i, dest in enumerate(dests, 1):
            exc = exc[f"--env=DST_{i}={dest}"]
        if dbs_to_include is not None:
            exc = exc[f"--env=DBS_TO_INCLUDE={dbs_to_include}"]
        if dbs_to_exclude is not None:
            exc = exc[f"--env=DBS_TO_EXCLUDE={dbs_to_exclude}"]
        exc = exc[duplicity_container]
        # Create all those test dbs
        list(map(exc["createdb"], existing_dbs))
        # Backup
        exc("/etc/periodic/daily/jobrunner")
        # Check backup files. Output looks like this:
        #   Local and Remote metadata are synchronized, no sync needed.
        #   Last full backup date: Fri Oct 29 12:29:35 2021
        #   Fri Oct 29 12:29:34 2021 .
        #   Fri Oct 29 12:29:34 2021 demo1.sql
        #   Fri Oct 29 12:29:34 2021 demo2.sql
        for dest in dests:
            output = exc("dup", "list-current-files", dest)
            backed = re.findall(r" (\w+)\.sql", output)
            assert backed == dbs_matched


@pytest.mark.parametrize(
    "dbs_matched, dests",
    (
        (
            ["prod1"],
            ["file:///mnt/backup/dst_1", "file:///mnt/backup/dst_2"],
        ),
    ),
)
def test_postgres_multi_restore(
    container_factory,
    postgres_container,
    dbs_matched: list,
    dests: list,
):
    with container_factory("postgres-multi") as duplicity_container:
        # Build docker exec command
        exc = docker[
            "exec",
            "--env=PGUSER=postgres",
            "--env=PGPASSWORD=password",
            "--env=PASSPHRASE=good",
            f"--env=PGHOST={postgres_container['NetworkSettings']['IPAddress']}",
            "--env=SRC=/mnt/backup/src",
        ]
        for i, dest in enumerate(dests, 1):
            exc = exc[f"--env=DST_{i}={dest}"]
        exc = exc[duplicity_container]
        # Create all those test dbs
        list(map(exc["createdb"], dbs_matched))
        # Backup
        exc("/etc/periodic/daily/jobrunner")
        exc("rm", "-rf", "/mnt/backup/src")
        with pytest.raises(Exception):
            output = exc("ls", "/mnt/backup/src")
        exc("restore")
        # Check restored files. Output looks like this:
        #   prod1.sql
        output = exc("ls", "/mnt/backup/src")
        backed = re.findall(r"\s?(\w+)\.sql", output)
        assert backed == dbs_matched
