#!/bin/bash

docker buildx use armbuilder
docker buildx inspect --bootstrap

latest=$(git describe --tags $(git rev-list --tags --max-count=1))

docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t cshackleton/senselink:$latest -t cshackleton/senselink:latest --push .