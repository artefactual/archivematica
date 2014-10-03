#!/usr/bin/env python2

import argparse
import sys

import django
django.setup()
# dashboard
from main import models

# archivematicaCommon
import storageService as storage_service

REJECTED = 'reject'
FAILED = 'fail'

def main(fail_type, sip_uuid):
    # Update SIP Arrange table for failed SIP
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list('uuid', flat=True)
    print 'Allow files in this SIP to be arranged. UUIDs:', file_uuids
    models.SIPArrange.objects.filter(sip_id=sip_uuid).delete()

    # Update storage service that reingest failed
    api = storage_service._storage_api()
    try:
        api.file(sip_uuid).patch({'reingest': None})
    except Exception:
        # Ignore errors, as this may not be reingest
        pass
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleanup from failed/rejected SIPs.')
    parser.add_argument('fail_type', help='"%s" or "%s"' % (REJECTED, FAILED))
    parser.add_argument('sip_uuid', help='%SIPUUID%')

    args = parser.parse_args()
    sys.exit(main(args.fail_type, args.sip_uuid))
