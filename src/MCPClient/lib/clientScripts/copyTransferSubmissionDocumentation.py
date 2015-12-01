#!/usr/bin/env python2

import os
import sys
import shutil

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.copyTransferSubmissionDocumentation")
    sipUUID = sys.argv[1]
    submissionDocumentationDirectory = sys.argv[2]
    sharedPath = sys.argv[3]

    transfer_locations = File.objects.filter(removedtime__isnull=True, sip_id=sipUUID, transfer__currentlocation__isnull=False).values_list('transfer__currentlocation').distinct()

    for transferLocation, in transfer_locations:
        transferLocation = transferLocation.replace("%sharedPath%", sharedPath)
        transferNameUUID = os.path.basename(os.path.abspath(transferLocation))
        src = os.path.join(transferLocation, "metadata/submissionDocumentation")
        dst = os.path.join(submissionDocumentationDirectory, "transfer-%s" % (transferNameUUID))
        print >>sys.stderr, src, " -> ", dst
        shutil.copytree(src, dst)
