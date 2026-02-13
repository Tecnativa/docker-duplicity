import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from time import sleep

import pytest
from plumbum import ProcessExecutionError, local
from plumbum.cmd import docker

_logger = logging.getLogger(__name__)


def pytest_configure():
    pytest.MIN_PG = "10"
    pytest.MAX_PG = "18"


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
    image_name = request.config.getoption("--image")

    # If running under pytest-xdist, make image tags unique per worker to avoid
    # concurrent "image already exists" collisions during docker build/export.
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id and worker_id != "master":
        image_name = f"{image_name}-{worker_id}"

    if request.config.getoption("--prebuild"):
        for tag in [
            "docker-s3",
            "postgres-s3",
            "postgres-multi",
            "docker",
            "postgres",
            "s3",
            "base",
        ]:
            image_full_name = f"{image_name}-{tag}"
            build = docker[
                "image",
                "build",
                "-t",
                image_full_name,
                "--target",
                tag,
                Path(__file__).parent.parent,
            ]
            retcode, stdout, stderr = build.run()
            _logger.log(
                logging.ERROR if retcode else logging.WARNING,
                "Build logs for COMMAND: %s\nEXIT CODE:%d\nSTDOUT:%s\nSTDERR:%s",
                build.bound_command(),
                retcode,
                stdout,
                stderr,
            )
            assert not retcode, "Image build failed"
    return image_name


@pytest.fixture(scope="session")
def container_factory(image):
    """A context manager that starts the docker container."""

    @contextmanager
    def _container(tag_name, dbver=None):
        container_id = None
        image_name = f"{image}-{tag_name}"
        _logger.info(f"Starting {image_name} container")
        try:
            docker_cmd = ["container", "run", "--detach"]
            if dbver:
                docker_cmd.append(f"--env=DB_VERSION={dbver}")
            docker_cmd.append(image_name)
            container_id = docker(*docker_cmd).strip()
            sleep(15)  # Wait for the service
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


def _normalize_inspect_ip(container_info: dict) -> dict:
    """Ensure container_info['NetworkSettings']['IPAddress'] exists.

    Newer Docker versions (and user-defined networks) may leave
    NetworkSettings.IPAddress empty / absent. The per-network IP lives in
    NetworkSettings.Networks[<name>].IPAddress.
    """
    ns = container_info.get("NetworkSettings") or {}
    # If IPAddress is already present and non-empty, keep it.
    ip = ns.get("IPAddress")
    if ip:
        return container_info

    networks = ns.get("Networks") or {}
    for net_data in networks.values():
        cand = (net_data or {}).get("IPAddress")
        if cand:
            ns["IPAddress"] = cand
            container_info["NetworkSettings"] = ns
            return container_info

    # No IP found; leave as-is (tests will fail with clearer error later).
    return container_info


@pytest.fixture
def postgres_factory():
    """Give a running postgres container ID."""

    @contextmanager
    def _container_info(dbver):
        container_id = docker(
            "container",
            "run",
            "--detach",
            "--env=POSTGRES_USER=postgres",
            "--env=POSTGRES_PASSWORD=password",
            f"postgres:{dbver or pytest.MIN_PG}-alpine",
        ).strip()
        container_info = json.loads(docker("container", "inspect", container_id))[0]
        container_info = _normalize_inspect_ip(container_info)
        for attempt in range(10):
            _logger.debug("Attempt %d of waiting for postgres to start.", attempt)
            try:
                docker(
                    "container", "exec", "--user=postgres", container_id, "psql", "-l"
                )
                break
            except ProcessExecutionError:
                sleep(3)
                if attempt == 9:
                    raise
        yield container_info
        _logger.info(f"Removing {container_id}...")
        docker("container", "rm", "-f", container_id)

    return _container_info
