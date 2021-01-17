#!/usr/bin/env bash

set -o errexit
set -o pipefail

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__hack="$(cd "$(dirname "${__dir}")" && pwd)"
__root="$(cd "$(dirname "${__hack}")" && pwd)"

docker buildx build ${__root} -f ${__hack}/Dockerfile -t amtest-server --build-arg TARGET=archivematica-mcp-server
docker buildx build ${__root} -f ${__hack}/Dockerfile -t amtest-client --build-arg TARGET=archivematica-mcp-client
docker buildx build ${__root} -f ${__hack}/Dockerfile -t amtest-dashboard --build-arg TARGET=archivematica-dashboard
