#!/usr/bin/env python2

import os
import sys

import django
django.setup()
# dashboard
from main.models import Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import renameAsSudo

def updateDB(dst, transferUUID):
    Transfer.objects.filter(uuid=transferUUID).update(currentlocation=dst)

def moveSIP(src, dst, transferUUID, sharedDirectoryPath):
    # os.rename(src, dst)
    if src.endswith("/"):
        src = src[:-1]

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))

    if os.path.isdir(src):
        dest += "/"
    updateDB(dest, transferUUID)

    renameAsSudo(src, dst)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.moveTransfer")

    src = sys.argv[1]
    dst = sys.argv[2]
    transferUUID = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    moveSIP(src, dst, transferUUID, sharedDirectoryPath)
