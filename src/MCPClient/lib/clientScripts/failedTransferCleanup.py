#!/usr/bin/env python2

from __future__ import print_function
import argparse
import os
import sys

import django
django.setup()

# archivematicaCommon
import storageService as storage_service

from main.models import File, Transfer

REJECTED = 'reject'
FAILED = 'fail'

def main(fail_type, transfer_uuid, transfer_path):
    # Update storage service that reingest failed
    api = storage_service._storage_api()
    aip_uuid = None
    # Get aip_uuid from reingest METS name
    if os.path.isdir(os.path.join(transfer_path, 'data')):
        mets_dir = os.path.join(transfer_path, 'data')
    elif os.path.isdir(os.path.join(transfer_path, 'metadata')):
        mets_dir = os.path.join(transfer_path, 'metadata')
    else:
        mets_dir = transfer_path
    for item in os.listdir(mets_dir):
        if item.startswith('METS'):
            aip_uuid = item.replace('METS.', '').replace('.xml', '')

    print('AIP UUID for this Transfer is', aip_uuid)
    try:
        api.file(aip_uuid).patch({'reingest': None})
    except Exception:
        # Ignore errors, as this may not be reingest
        pass

    # Delete files for reingest transfer
    # A new reingest doesn't know to delete this because the UUID is different from the AIP, and it causes problems when re-parsing these files
    transfer = Transfer.objects.get(uuid=transfer_uuid)
    if transfer.type == 'Archivematica AIP':
        File.objects.filter(transfer_id=transfer_uuid).delete()
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleanup from failed/rejected SIPs.')
    parser.add_argument('fail_type', help='"%s" or "%s"' % (REJECTED, FAILED))
    parser.add_argument('transfer_uuid', help='%SIPUUID%')
    parser.add_argument('transfer_path', help='%SIPDirectory%')

    args = parser.parse_args()
    sys.exit(main(args.fail_type, args.transfer_uuid, args.transfer_path))
