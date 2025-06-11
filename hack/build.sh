#!/usr/bin/env bash

set -xeo pipefail

DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR=$(pwd)

docker build \
    --target "archivematica-mcp-server" \
    --tag "archivematica-mcp-server" \
    --file $DIR/Dockerfile .

docker build \
    --target "archivematica-mcp-client" \
    --tag "archivematica-mcp-client" \
    --file $DIR/Dockerfile .

docker build \
    --target "archivematica-dashboard" \
    --tag "archivematica-dashboard" \
    --file $DIR/Dockerfile .

docker image tag archivematica-mcp-server "artefactual/archivematica-mcp-server:qa.1.x"
docker image tag archivematica-mcp-client "artefactual/archivematica-mcp-client:qa.1.x"
docker image tag archivematica-dashboard "artefactual/archivematica-dashboard:qa.1.x"
