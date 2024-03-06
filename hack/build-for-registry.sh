#!/usr/bin/env bash

set -xeo pipefail

DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR=$(pwd)

docker build \
    --target "archivematica-mcp-server" \
    --tag "artefactual/archivematica-mcp-server" \
    --file $DIR/Dockerfile .

docker build \
    --target "archivematica-mcp-client" \
    --tag "artefactual/archivematica-mcp-client" \
    --file $DIR/Dockerfile .

docker build \
    --target "archivematica-dashboard" \
    --tag "artefactual/archivematica-dashboard" \
    --file $DIR/Dockerfile .

if [[ ! -z "${PUSH_DOCKER}" ]]
then
    docker push artefactual/archivematica-dashboard
    docker push artefactual/archivematica-mcp-client
    docker push artefactual/archivematica-mcp-server
fi

