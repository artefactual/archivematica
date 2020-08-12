#!/usr/bin/env bash

set -o errexit
set -o pipefail

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__root="$(cd "$(dirname "${__dir}")" && pwd)"

function count_migrations() {
    ls ${__root}/src/dashboard/src/main/migrations/*.py | wc -l
}

MIGRATIONS_COUNT_BEFORE=$(count_migrations)
${__root}/src/dashboard/src/manage.py makemigrations
MIGRATIONS_COUNT_AFTER=$(count_migrations)

if [ $MIGRATIONS_COUNT_BEFORE -ne $MIGRATIONS_COUNT_AFTER ]; then
    echo "Migrations are needed"
    exit 1
fi
