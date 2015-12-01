#!/usr/bin/env python2

import os
import sys
import lxml.etree as etree

# fileOperations requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import updateFileLocation
from fileOperations import renameAsSudo

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory="./"):
    print metsFile
    DSpaceMets = "metadata/submissionDocumentation/DSpaceMets"
    try:
        path = os.path.join(transferDirectory, DSpaceMets)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        print "error creating DSpaceMets directory."
    exitCode = 0

    metsDirectory = os.path.basename(os.path.dirname(metsFile))

    if metsDirectory == "DSpace_export":
        outputDirectory = path
    else:
        outputDirectory = os.path.join(path, metsDirectory)
        if not os.path.isdir(outputDirectory):
            os.mkdir(outputDirectory)

    dest = os.path.join(outputDirectory, "mets.xml")
    renameAsSudo(metsFile, dest)

    src = metsFile.replace(transferDirectory, "%transferDirectory%")
    dst = dest.replace(transferDirectory, "%transferDirectory%")
    eventDetail = ""
    eventOutcomeDetailNote = "moved from=\"" + src + "\"; moved to=\"" + dst + "\""
    updateFileLocation(src, dst, "movement", date, eventDetail, transferUUID=transferUUID, eventOutcomeDetailNote = eventOutcomeDetailNote)

    return exitCode



if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.moveDspaceMetsFilesToDSpaceMETS")

    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]
    transferDirectory = sys.argv[4]
    transferUUID = sys.argv[5]


    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
