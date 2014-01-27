#!/usr/bin/python -OO

import csv
import json
import os
import sys


def fetch_keys(objects):
    keys = set()
    for object in objects:
        keys.update(object.keys())

    # Column order is otherwise unimportant, but
    # "filename" and "parts" must be column 0.
    # (They are mutually exclusive.)
    keys = list(keys)
    if 'filename' in keys:
        keys.remove('filename')
        keys.insert(0, 'filename')
    elif 'parts' in keys:
        keys.remove('parts')
        keys.insert(0, 'parts')

    return keys


# DictWriter will fail if any Unicode characters are in the keys or
# values in a dict passed to writerow(). This encodes them all to
# UTF-8 bytestrings.
def fix_encoding(row):
    return {key.encode('utf-8'): value.encode('utf-8') for key, value in row.iteritems()}


def main(sip_uuid, json_metadata):
    # Many transfers won't have JSON metadata, so just exit without
    # any further processing if that's the case
    if not os.path.exists(json_metadata):
        return 0

    with open(json_metadata) as data:
        parsed = json.load(data)

    basename, _ = os.path.splitext(json_metadata)
    output = basename + '.csv'

    with open(output, 'w') as dest:
        writer = csv.DictWriter(dest, fetch_keys(parsed))
        writer.writeheader()
        for row in parsed:
            writer.writerow(fix_encoding(row))

    return 0

if __name__ == '__main__':
    try:
        sip_uuid, json_metadata = sys.argv[1:]
    except ValueError:
        sys.exit("SIP UUID or path to JSON metadata not provided!")

    sys.exit(main(sip_uuid, json_metadata))
