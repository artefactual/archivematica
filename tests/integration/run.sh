#!/usr/bin/env bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd ${__dir}

# Service that runs pytest. Authentication integration suites use dedicated
# services because their Django settings cannot all be enabled together.
INTEGRATION_SERVICE="${INTEGRATION_SERVICE:-archivematica-dashboard}"

if [ -z "${SKIP_DOCKER_BUILD}" ]; then
    case "${INTEGRATION_SERVICE}" in
        archivematica-dashboard-cas)
            # The CAS service reuses the image built by the default service.
            docker compose build archivematica-dashboard cas
            ;;
        archivematica-dashboard-ldap)
            # The LDAP service reuses the image built by the default service.
            docker compose build archivematica-dashboard
            ;;
        archivematica-dashboard-shibboleth)
            # The Shibboleth service reuses the image built by the default service.
            docker compose build archivematica-dashboard shibboleth-sp
            ;;
        *)
            docker compose build "${INTEGRATION_SERVICE}"
            ;;
    esac

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
