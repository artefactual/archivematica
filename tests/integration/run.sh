#!/usr/bin/env bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${__dir}

docker compose build archivematica-dashboard

status=$?

if [ $status -ne 0 ]; then
    exit $status
fi

docker compose run --rm archivematica-dashboard

status=$?

if [ -z "${REUSE_TEST_ENV}" ]; then
    docker compose down --volumes
fi

exit $status
