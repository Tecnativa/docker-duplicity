import json
import logging
from contextlib import contextmanager
from pathlib import Path
from time import sleep

import pytest
from plumbum import ProcessExecutionError, local
from plumbum.cmd import docker

MIN_PG = 13.0

_logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Allow prebuilding image for local testing."""
    parser.addoption(
        "--prebuild",
        action="store_true",
        help="Build local image before testing",
    )
    parser.addoption(
        "--image",
        action="store",
        default="test:docker-duplicity",
        help="Specify testing image name",
    )


@pytest.fixture(scope="session")
def image(request):
    """Get image name. Builds it if needed."""
    image = request.config.getoption("--image")
    images = []
    if request.config.getoption("--prebuild"):
        for tag in ["docker-s3", "postgres-s3", "docker", "postgres", "s3", "base"]:
            image_name = f"{image}-{tag}"
            images.append(image_name)
            build = docker[
                "image",
                "build",
                "-t",
                image_name,
                "--target",
                tag,
                Path(__file__).parent.parent,
            ]
            retcode, stdout, stderr = build.run()
            _logger.log(
                # Pytest prints warnings if a test fails, so this is a warning if
                # the build succeeded, to allow debugging the build logs
                logging.ERROR if retcode else logging.WARNING,
                "Build logs for COMMAND: %s\nEXIT CODE:%d\nSTDOUT:%s\nSTDERR:%s",
                build.bound_command(),
                retcode,
                stdout,
                stderr,
            )
            assert not retcode, "Image build failed"
    return image


@pytest.fixture(scope="session")
def container_factory(image):
    """A context manager that starts the docker container."""

    @contextmanager
    def _container(tag_name):
        container_id = None
        image_name = f"{image}-{tag_name}"
        _logger.info(f"Starting {image_name} container")
        try:
            container_id = docker(
                "container",
                "run",
                "--detach",
                image_name,
            ).strip()
            with local.env():
                yield container_id
        finally:
            if container_id:
                _logger.info(f"Removing {container_id}...")
                docker(
                    "container",
                    "rm",
                    "-f",
                    container_id,
                )

    return _container


@pytest.fixture
def postgres_container():
    """Give a running postgres container ID."""
    container_id = docker(
        "container",
        "run",
        "--detach",
        "--env=POSTGRES_USER=postgres",
        "--env=POSTGRES_PASSWORD=password",
        f"postgres:{MIN_PG}-alpine",
    ).strip()
    container_info = json.loads(docker("container", "inspect", container_id))[0]
    for attempt in range(10):
        _logger.debug("Attempt %d of waiting for postgres to start.", attempt)
        try:
            docker("container", "exec", "--user=postgres", container_id, "psql", "-l")
            break
        except ProcessExecutionError:
            sleep(3)
            if attempt == 9:
                raise
    yield container_info
    _logger.info(f"Removing {container_id}...")
    docker("container", "rm", "-f", container_id)
