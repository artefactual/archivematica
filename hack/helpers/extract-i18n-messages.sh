#!/usr/bin/env bash

# TODO: this script runs multiple commands inside Archivematica and it makes
# assumptions on how things work and need to be executed. This dependency is
# undesirable and should be refactored at some point, e.g. we could have a
# simple `Makefile` in each of the repos and a target like `i18n-extract`,
# `i18n-push`, etc...

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

echo "Dashboard: extracting messages..."
dashboard::manage makemessages --all --domain django
dashboard::manage makemessages --all --domain djangojs --ignore build/*

docker-compose run \
	--user=$(id -u):$(id -g) \
	--rm --no-deps \
	--workdir=/src/src/dashboard/frontend \
	--entrypoint=yarn \
		archivematica-dashboard run extract-messages

(cd ${__root_dir} && git status -s)


#
# Storage Service
#

echo "Storage Service: extracting messages..."
storage::manage makemessages --all --domain django
storage::manage makemessages --all --domain djangojs

(cd ${__root_dir}/hack/submodules/archivematica-storage-service && git status -s)

# Not ready yet:
# - fpr-admin
