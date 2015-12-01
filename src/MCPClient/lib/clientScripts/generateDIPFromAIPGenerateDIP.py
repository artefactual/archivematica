#!/usr/bin/env python2

import os
import sys
import shutil

import django
django.setup()
# dashboard
from main.models import Job, SIP

# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import createSIP

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.generateDIPFromAIPGenerateDIP")

    # COPY THE METS FILE
    # Move the DIP Directory

    fauxUUID = sys.argv[1]
    unitPath = sys.argv[2]
    date = sys.argv[3]

    basename = os.path.basename(unitPath[:-1])
    uuidLen = 36
    originalSIPName = basename[:-(uuidLen+1)*2]
    originalSIPUUID = basename[:-(uuidLen+1)][-uuidLen:]
    METSPath = os.path.join(unitPath, "metadata/submissionDocumentation/data/", "METS.%s.xml" % (originalSIPUUID))
    if not os.path.isfile(METSPath):
        print >>sys.stderr, "Mets file not found: ", METSPath
        exit(-1)

    # move mets to DIP
    src = METSPath
    dst = os.path.join(unitPath, "DIP", os.path.basename(METSPath))
    shutil.move(src, dst)

    # Move DIP
    src = os.path.join(unitPath, "DIP")
    dst = os.path.join("/var/archivematica/sharedDirectory/watchedDirectories/uploadDIP/", originalSIPName + "-" + originalSIPUUID)  
    shutil.move(src, dst)

    try:
        SIP.objects.get(uuid=originalSIPUUID)
    except SIP.DoesNotExist:
        # otherwise doesn't appear in dashboard
        createSIP(unitPath, UUID=originalSIPUUID)
        Job.objects.create(jobtype="Hack to make DIP Jobs appear",
                           directory=unitPath,
                           sip_id=originalSIPUUID,
                           currentstep="Completed successfully",
                           unittype="unitSIP",
                           microservicegroup="Upload DIP")
