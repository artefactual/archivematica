#!/usr/bin/env python2

import os
import shutil
import sys

import django
django.setup()
# dashboard
from main.models import SIP

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import renameAsSudo

def updateDB(dst, sip_uuid):
    SIP.objects.filter(uuid=sip_uuid).update(currentpath=dst)

def moveSIP(src, dst, sipUUID, sharedDirectoryPath):
    # Prepare paths
    if src.endswith("/"):
        src = src[:-1]

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))
    updateDB(dest + "/", sipUUID)

    # If destination already exists, delete it with warning
    dest_path = os.path.join(dst, os.path.basename(src))
    if os.path.exists(dest_path):
        print >>sys.stderr, dest_path, 'exists, deleting'
        shutil.rmtree(dest_path)

    renameAsSudo(src, dst)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.moveSIP")

    src = sys.argv[1]
    dst = sys.argv[2]
    sipUUID = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    moveSIP(src, dst, sipUUID, sharedDirectoryPath)
