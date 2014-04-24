#!/usr/bin/python -OO

import csv
import json
import os
import sys


def fetch_keys(objects):
    """
    Returns a list of keys in a set of dicts suitable for use as a
    CSV header row.
    If values in the dict are lists, then the header row will contain
    N occurrences of the key, where N is the largest list under that
    key in the set of dicts.
    """
    # Track the occurrence of each set of keys; we'll need to produce
    # one column for each occurrence of that key if its value in the
    # JSON object is an array.
    occurrence_count = {}
    keys = set()

    for o in objects:
        o_keys = o.keys()
        for key in o_keys:
            if isinstance(o[key], list):
                occurrence = len(o[key])
                if key not in occurrence_count or occurrence_count[key] < occurrence:
                    occurrence_count[key] = occurrence
        keys.update(o_keys)

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

    # now we need to update the list to ensure there are the right numbers
    # of occurrences.
    for key, count in occurrence_count.iteritems():
        index = keys.index(key) + 1
        for _ in range(count - 1):
            keys.insert(index, key)

    return keys


def shallow_flatten(array):
    out = []
    for item in array:
        if isinstance(item, (list, tuple, set)):
            for i in item:
                out.append(i)
        else:
            out.append(item)
    return out


def encode_item(item):
    """
    Wraps str.encode by recursively encoding lists.
    """
    if isinstance(item, basestring):
        return item.encode('utf-8')
    else:
        return [i.encode('utf-8') for i in item]


def fix_encoding(row):
    """
    Python's CSV writers will fail if any Unicode characters are in the
    keys or values passed to writerow(). This encodes them all to
    UTF-8 bytestrings.
    """
    return {key.encode('utf-8'): encode_item(value) for key, value in row.iteritems()}


def object_to_row(row, headers):
    """
    Takes a dict and returns a row suitable for serialization to CSV.
    The `headers` argument is mandatory and determines the order
    of values.
    """
    def sort_row(keyvalue):
        return headers.index(keyvalue[0])
    row = sorted(row.items(), key=sort_row)
    row = [kv[1] for kv in row]
    return shallow_flatten(row)


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
        # Note that we unfortunately can't use DictWriter here because of
        # the unusual way in which we deal with repeated items.
        # The JSON handles multiple occurrences of a subject via an array,
        # for instance {'dc.subject': ['foo', 'bar', 'baz']}
        # In CSV, we handle this by repeating the column. DictWriter is not
        # really capable of handling this.
        writer = csv.writer(dest)
        headers = fetch_keys(parsed)
        writer.writerow(headers)
        for row in parsed:
            writer.writerow(object_to_row(fix_encoding(row), headers))

    return 0

if __name__ == '__main__':
    try:
        sip_uuid, json_metadata = sys.argv[1:]
    except ValueError:
        sys.exit("SIP UUID or path to JSON metadata not provided!")

    sys.exit(main(sip_uuid, json_metadata))
