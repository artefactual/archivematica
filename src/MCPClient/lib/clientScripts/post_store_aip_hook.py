#!/usr/bin/python2 -OO

import argparse
import sys

# archivematicaCommon
import elasticSearchFunctions
import storageService as storage_service

# dashboard
from main import models

def post_store_hook(sip_uuid):
    """
    Hook for doing any work after an AIP is stored successfully.
    """

    # SIP ARRANGEMENT

    # Mark files in this SIP as in an AIP (aip_created)
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list('uuid', flat=True)
    models.SIPArrange.objects.filter(file_uuid__in=file_uuids).update(aip_created=True)

    # Check if any of component transfers are completely stored
    # TODO Storage service should index AIPs, knows when to update ES
    transfer_uuids = set(models.SIPArrange.objects.filter(file_uuid__in=file_uuids).values_list('transfer_uuid', flat=True))
    for transfer_uuid in transfer_uuids:
        print 'Checking if transfer', transfer_uuid, 'is fully stored...'
        arranged_uuids = set(models.SIPArrange.objects.filter(transfer_uuid=transfer_uuid).filter(aip_created=True).values_list('file_uuid', flat=True))
        backlog_uuids = set(models.File.objects.filter(transfer=transfer_uuid).values_list('uuid', flat=True))
        # If all backlog UUIDs have been arranged
        if arranged_uuids == backlog_uuids:
            print 'Transfer', transfer_uuid, 'fully stored, sending delete request to storage service, deleting from transfer backlog'
            # Submit delete req to SS (not actually delete), remove from ES
            storage_service.request_file_deletion(
                uuid=transfer_uuid,
                user_id=0,
                user_email='archivematica system',
                reason_for_deletion='All files in Transfer are now in AIPs.'
            )
            elasticSearchFunctions.connect_and_remove_transfer_files(transfer_uuid)

    # POST-STORE CALLBACK
    storage_service.post_store_aip_callback(sip_uuid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sip_uuid', help='%SIPUUID%')

    args = parser.parse_args()
    sys.exit(post_store_hook(args.sip_uuid))
