#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import json
import os
import sys

from six.moves import zip

FILES = ["pii", "ccn"]
HEADERS = ["offset", "content", "context"]


def main(uuid, log_path, output):
    features = {}

    path = os.path.normpath(os.path.join(log_path, "bulk-" + uuid))
    for name in FILES:
        filepath = os.path.join(path, name + ".txt")
        with open(filepath) as f:
            data = f.read()

        features[name] = [
            dict(list(zip(HEADERS, line.split("\t"))))
            for line in data.splitlines()
            if not line.startswith("#")
        ]

    with open(os.path.join(output, uuid), "w") as outfile:
        print(json.dumps(features, indent=2), file=outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Bulk Extractor logs into fixture JSON"
    )
    parser.add_argument(
        "log_path", help="Directory containing Bulk Extractor logs to parse"
    )
    parser.add_argument("uuid", help="UUID of the file whose logs should be parsed")
    parser.add_argument(
        "output", help="Directory to which fixture files should be written"
    )
    args = parser.parse_args()

    try:
        sys.exit(main(args.uuid, args.log_path, args.output))
    except Exception as e:
        sys.exit(e)
