#!/bin/bash
#
# Enable Python 3 versions to be compiled and installed on a Bionic image.
#
#   Based on: https://github.com/matthewfeickert/Docker-Python3-Ubuntu/
#
set -eux

function main() {

    # If we're not installing Python 3 we can ignore the rest of this script.
    PYTHON_3="${1}"
    if [[ "${PYTHON_3}" == "false" ]]; then
        echo "Not installing Python 3"
        exit 0
    fi

    if [[ -z "${2}" ]]; then
        echo "Python major version isn't set"
        exit 1
    fi

    if [[ -z "${3}" ]]; then
        echo "Python version tag isn't set"
        exit 1
    fi

    PYTHON_MAJOR_VERSION="${2}"
    PYTHON_VERSION_TAG="${3}"

    cd /usr/src
    apt-get update
    apt-get install wget
    wget https://www.python.org/ftp/python/"${PYTHON_VERSION_TAG}"/Python-"${PYTHON_VERSION_TAG}".tgz
    tar xzf Python-"${PYTHON_VERSION_TAG}".tgz
    cd Python-"${PYTHON_VERSION_TAG}"
    ./configure --enable-optimizations
    make install

    # Create symlinks to the newly installed Python versions.
    ln -s -f /usr/local/bin//python"${PYTHON_MAJOR_VERSION}" /usr/bin/python
    ln -s -f /usr/local/bin/pip3 /usr/local/bin/pip

}

main "$@" || exit 1
