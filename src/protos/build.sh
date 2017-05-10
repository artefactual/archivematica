#!/usr/bin/env bash

# You need grpcio-tools installed on your machine for this script to work!
# See https://developers.google.com/protocol-buffers/docs/reference/python-generated

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__output="${__dir}/../archivematicaCommon/lib/protos/"

python -m grpc.tools.protoc -I${__dir} --python_out=${__output} --grpc_python_out=${__output} ${__dir}/*.proto
