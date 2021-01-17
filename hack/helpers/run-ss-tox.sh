#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__compose_dir="$(cd "$(dirname "${__dir}")" && pwd)"

cd ${__compose_dir}

# We use --no-deps because MySQL is not needed as long as we're testing against
# the sqlite3 memory backend (see storage_service.settings.test module).

docker-compose run --rm --no-deps --entrypoint tox \
	-e "DJANGO_SETTINGS_MODULE=storage_service.settings.test" \
		archivematica-storage-service "$@"
