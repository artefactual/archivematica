#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__compose_dir="$(cd "$(dirname "${__current_dir}")" && pwd)"
__root_dir="$(cd "$(dirname "${__compose_dir}")" && pwd)"

cd ${__compose_dir}

function dashboard::manage {
	docker-compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/dashboard/src \
		--entrypoint=/src/src/dashboard/src/manage.py \
			archivematica-dashboard "$@"
}

function storage::manage {
	docker-compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/storage_service \
		--entrypoint=/src/storage_service/manage.py \
			archivematica-storage-service "$@"
}


#
# Dashboard
#

echo "Dashboard: compiling messages..."
dashboard::manage compilemessages


#
# Storage Service
#

echo "Storage Service: compiling messages..."
storage::manage compilemessages
