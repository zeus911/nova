#!/usr/bin/env bash

set -e

docker ps -aq | xargs -r docker stop
docker ps -aq | xargs -r docker rm -v
