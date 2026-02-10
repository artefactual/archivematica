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

only=""
for arg in "$@"; do
	case "$arg" in
	--only=am|--only=ss)
		only="${arg#--only=}"
		;;
	--only=*)
		echo "Invalid value for --only. Use --only=am or --only=ss" >&2
		exit 2
		;;
	*)
		echo "Unknown argument: $arg" >&2
		echo "Usage: $0 [--only=am|ss]" >&2
		exit 2
		;;
	esac
done

function dashboard::manage {
	docker compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/archivematica/dashboard \
		--entrypoint=/src/src/archivematica/dashboard/manage.py \
			archivematica-dashboard "$@"
}

function storage::manage {
	docker compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/archivematica/storage_service \
		--entrypoint=/src/src/archivematica/storage_service/manage.py \
			archivematica-storage-service "$@"
}


#
# Dashboard
#

if [[ -z "$only" || "$only" == "am" ]]; then
	echo "Dashboard: extracting messages..."
	dashboard::manage makemessages --all --domain django --no-obsolete
	dashboard::manage makemessages --all --domain djangojs --ignore dist/* --ignore node_modules/* --no-obsolete

	(cd ${__root_dir} && git status -s)
fi


#
# Storage Service
#

if [[ -z "$only" || "$only" == "ss" ]]; then
	echo "Storage Service: extracting messages..."
	storage::manage makemessages --all --domain django --no-obsolete
	storage::manage makemessages --all --domain djangojs --no-obsolete

	(cd ${__root_dir}/hack/submodules/archivematica-storage-service && git status -s)
fi

# Not ready yet:
# - fpr-admin
