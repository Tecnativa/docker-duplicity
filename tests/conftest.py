import os
from contextlib import contextmanager
from logging import info
from pathlib import Path

import pytest
from plumbum import local
from plumbum.cmd import docker

DOCKER_IMAGE_NAME = os.environ.get("DOCKER_IMAGE_NAME", "docker-duplicity-local")


def pytest_addoption(parser):
    """Allow prebuilding image for local testing."""
    parser.addoption("--prebuild", action="store_const", const=True)


@pytest.fixture(autouse=True, scope="session")
def prebuild_docker_image(request):
    """Build local docker image once before starting test suite."""
    if request.config.getoption("--prebuild"):
        for tag in ["docker-s3", "postgres-s3", "docker", "postgres", "latest"]:
            docker_image_name = f"{DOCKER_IMAGE_NAME}:{tag}"
            info(f"Building {docker_image_name}...")
            docker(
                "build",
                "-t",
                docker_image_name,
                "--target",
                tag,
                str(Path(__file__).parent.parent),
            )


@contextmanager
def container(tag_name):
    """A context manager that starts the docker container."""
    container_id = None
    docker_image_name = f"{DOCKER_IMAGE_NAME}:{tag_name}"
    info(f"Starting {docker_image_name} container")
    try:
        container_id = docker(
            "container",
            "run",
            "--detach",
            docker_image_name,
        ).strip()
        with local.env():
            yield container_id
    finally:
        if container_id:
            info(f"Removing {container_id}...")
            docker(
                "container",
                "rm",
                "-f",
                container_id,
            )
