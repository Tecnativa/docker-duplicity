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
