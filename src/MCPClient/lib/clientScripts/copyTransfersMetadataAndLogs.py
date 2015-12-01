#!/usr/bin/env python2

import os
import sys
import shutil
from optparse import OptionParser
import traceback

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger


def main(sipUUID, transfersMetadataDirectory, transfersLogsDirectory, sharedPath=""):
    if not os.path.exists(transfersMetadataDirectory):
        os.makedirs(transfersMetadataDirectory)
    if not os.path.exists(transfersLogsDirectory):
        os.makedirs(transfersLogsDirectory)

    exitCode = 0

    files = File.objects.filter(sip_id=sipUUID, transfer__isnull=False).order_by('transfer__uuid').values_list('transfer__uuid', 'transfer__currentlocation')
    for transferUUID, transferPath in files:
        try:
            if sharedPath != "":
                transferPath = transferPath.replace("%sharedPath%", sharedPath, 1)
            transferBasename = os.path.basename(os.path.abspath(transferPath))
            transferMetaDestDir = os.path.join(transfersMetadataDirectory, transferBasename)
            transfersLogsDestDir = os.path.join(transfersLogsDirectory, transferBasename)
            if not os.path.exists(transferMetaDestDir):
                os.makedirs(transferMetaDestDir)
                transferMetadataDirectory = os.path.join(transferPath, "metadata")
                for met in os.listdir(transferMetadataDirectory):
                    if met == "submissionDocumentation":
                        continue
                    item = os.path.join(transferMetadataDirectory, met)
                    if os.path.isdir(item):
                        shutil.copytree(item, os.path.join(transferMetaDestDir, met))
                    else:
                        shutil.copy(item, os.path.join(transferMetaDestDir, met))
                print "copied: ", transferPath + "metadata", " -> ", os.path.join(transferMetaDestDir, "metadata")
            if not os.path.exists(transfersLogsDestDir):
                os.makedirs(transfersLogsDestDir)
                shutil.copytree(transferPath + "logs", os.path.join(transfersLogsDestDir, "logs"))
                print "copied: ", transferPath + "logs", " -> ", os.path.join(transfersLogsDestDir, "logs")
                

        except Exception as inst:
            traceback.print_exc(file=sys.stderr)
            exitCode += 1

    exit(exitCode)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.copyTransfersMetadataAndLogs")

    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)
    parser = OptionParser()
    parser.add_option("-s",  "--sipDirectory", action="store", dest="sipDirectory", default="")
    parser.add_option("-S",  "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-p",  "--sharedPath", action="store", dest="sharedPath", default="/var/archivematica/sharedDirectory/")
    (opts, args) = parser.parse_args()


    main(opts.sipUUID, opts.sipDirectory+"metadata/transfers/", opts.sipDirectory+"logs/transfers/", sharedPath=opts.sharedPath)
