#!/bin/bash
# See https://github.com/docker/hub-feedback/issues/508#issuecomment-222520720.
set -x

# Get only version name
version="$(echo $IMAGE_NAME | sed 's/.*://')"

# Apply when it is not empty nor "latest"
if [ -n "$version" -a "$version" != "latest" ]; then
    args=--build-arg DUPLICITY_VERSION=$version
fi

docker build $arg --tag $IMAGE_NAME .
