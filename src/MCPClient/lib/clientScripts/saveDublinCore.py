#!/usr/bin/python2

import json
import sys

# dashboard
from main import models

FIELDS = [
    'title', 'creator', 'subject', 'description', 'publisher', 'contributor',
    'date', 'type', 'format', 'identifier', 'source', 'relation', 'language',
    'coverage', 'rights'
]


def main(transfer_uuid, target_path):
    jsonified = {}
    try:
        dc = models.DublinCore.objects.get(metadataappliestoidentifier=transfer_uuid)
    except:
        # There may not be any DC metadata for this transfer, and that's fine
        print >> sys.stderr, "No DC metadata found; skipping"
        return 0
    for field in FIELDS:
        attr = getattr(dc, field)
        if attr:
            jsonified[field] = attr

    print "Saving the following properties to:", target_path
    print jsonified

    with open(target_path, 'w') as json_file:
        json.dump(jsonified, json_file)
    return 0

if __name__ == '__main__':
    transfer_uuid = sys.argv[1]
    target_path = sys.argv[2]
    sys.exit(main(transfer_uuid, target_path))
