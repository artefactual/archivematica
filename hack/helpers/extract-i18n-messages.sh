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
clear_fuzzy=false
for arg in "$@"; do
	case "$arg" in
	--only=am|--only=ss)
		only="${arg#--only=}"
		;;
	--clear-fuzzy)
		clear_fuzzy=true
		;;
	--only=*)
		echo "Invalid value for --only. Use --only=am or --only=ss" >&2
		exit 2
		;;
	*)
		echo "Unknown argument: $arg" >&2
		echo "Usage: $0 [--only=am|ss] [--clear-fuzzy]" >&2
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

function dashboard::shell {
	docker compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/archivematica/dashboard \
		--entrypoint=/bin/bash \
			archivematica-dashboard -lc "$1"
}

function storage::manage {
	docker compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/archivematica/storage_service \
		--entrypoint=/src/src/archivematica/storage_service/manage.py \
			archivematica-storage-service "$@"
}

function storage::shell {
	docker compose run \
		--user=$(id -u):$(id -g) \
		--rm --no-deps \
		--workdir=/src/src/archivematica/storage_service \
		--entrypoint=/bin/bash \
			archivematica-storage-service -lc "$1"
}

#
# Dashboard
#

if [[ -z "$only" || "$only" == "am" ]]; then
	echo "Dashboard: extracting messages..."
	dashboard::manage makemessages --all --domain django --no-obsolete
	dashboard::manage makemessages --all --domain djangojs --ignore dist/* --ignore node_modules/* --no-obsolete
	if [[ "$clear_fuzzy" == "true" ]]; then
		echo "Dashboard: clearing fuzzy entries..."
		dashboard::shell 'find locale -name "*.po" -print0 | xargs -0 -I{} msgattrib --clear-fuzzy --no-obsolete -o "{}" "{}"'
	fi

	(cd ${__root_dir} && git status -s)
fi


#
# Storage Service
#

if [[ -z "$only" || "$only" == "ss" ]]; then
	echo "Storage Service: extracting messages..."
	storage::manage makemessages --all --domain django --no-obsolete
	storage::manage makemessages --all --domain djangojs --no-obsolete
	if [[ "$clear_fuzzy" == "true" ]]; then
		echo "Storage Service: clearing fuzzy entries..."
		storage::shell 'find locale -name "*.po" -print0 | xargs -0 -I{} msgattrib --clear-fuzzy --no-obsolete -o "{}" "{}"'
	fi

	(cd ${__root_dir}/hack/submodules/archivematica-storage-service && git status -s)
fi

# Not ready yet:
# - fpr-admin
