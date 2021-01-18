import logging

from conftest import container
from plumbum.cmd import docker

logger = logging.getLogger()


def test_containers_start():
    for tag in ["docker-s3", "postgres-s3", "docker", "postgres", "latest"]:
        with container(tag) as test_container:
            docker(
                "exec",
                test_container,
                "dup",
                "--version",
            )
def test_docker_bin():
    for tag in ["docker-s3", "docker"]:
        with container(tag) as test_container:
            docker(
                "exec",
                test_container,
                "docker",
                "--version",
            )
def test_postgres_bin():
    for tag in ["postgres-s3", "postgres"]:
        with container(tag) as test_container:
            docker(
                "exec",
                test_container,
                "psql",
                "--version",
            )
