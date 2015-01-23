#!/usr/bin/python2

import json
import os
import sys

# dashboard
from main import models

# This is the UUID of SIP from the `MetadataAppliesToTypes` table
INGEST_METADATA_TYPE = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'


def main(sip_uuid, dc_path):
    # If there's no metadata, that's not an error, and just keep going
    if not os.path.exists(dc_path):
        print "DC metadata not found; exiting", "(at", dc_path + ")"
        return 0

    print "Loading DC metadata from", dc_path
    with open(dc_path) as json_data:
        data = json.load(json_data)
    dc = models.DublinCore(metadataappliestoidentifier=sip_uuid,
                           metadataappliestotype_id=INGEST_METADATA_TYPE)
    for key, value in data.iteritems():
        try:
            setattr(dc, key, value)
        except AttributeError:
            print >> sys.stderr, "Invalid DC attribute:", key

    dc.save()
    return 0

if __name__ == '__main__':
    sip_uuid = sys.argv[1]
    dc_path = sys.argv[2]
    sys.exit(main(sip_uuid, dc_path))
