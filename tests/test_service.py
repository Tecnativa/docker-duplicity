import logging

from plumbum.cmd import docker

MIN_PG = 13.0


def test_containers_start(container_factory):
    for tag in ["docker-s3", "postgres-s3", "docker", "postgres", "latest"]:
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
