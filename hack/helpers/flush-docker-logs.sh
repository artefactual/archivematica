#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__compose_dir="$(cd "$(dirname "${__dir}")" && pwd)"

cd ${__compose_dir}

if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root."
    exit
fi

for container_id in $(docker-compose ps --quiet); do
    logpath=$(docker inspect --format='{{.LogPath}}' ${container_id})
    echo "Removing ${logpath}..."
    echo '' > $(docker inspect --format='{{.LogPath}}' ${container_id})
done
