#!/usr/bin/env bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${__dir}

# Service that runs pytest. Use archivematica-dashboard-cas to run the CAS
# authentication test suite instead of the default one.
INTEGRATION_SERVICE="${INTEGRATION_SERVICE:-archivematica-dashboard}"

if [ -z "${SKIP_DOCKER_BUILD}" ]; then
    if [ "${INTEGRATION_SERVICE}" == "archivematica-dashboard-cas" ]; then
        # The CAS service reuses the image built by the default service.
        docker compose build archivematica-dashboard cas
    else
        docker compose build "${INTEGRATION_SERVICE}"
    fi

    status=$?

    if [ $status -ne 0 ]; then
        exit $status
    fi
fi

docker compose run --rm "${INTEGRATION_SERVICE}"

status=$?

if [ -z "${REUSE_TEST_ENV}" ]; then
    docker compose down --volumes
fi

exit $status
