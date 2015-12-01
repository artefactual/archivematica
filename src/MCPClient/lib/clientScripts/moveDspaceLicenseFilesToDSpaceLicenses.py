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
    DspaceLicenses = "metadata/submissionDocumentation/DspaceLicenses"
    try:
        path = os.path.join(transferDirectory, DspaceLicenses)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        print "error creating DspaceLicenses directory."
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp"):
        #print etree.tostring(item)
        #print item

        USE = item.get("USE")
        if USE == "LICENSE":
            for item2 in item:
                if item2.tag == "{http://www.loc.gov/METS/}file":
                    for item3 in item2:
                        if item3.tag == "{http://www.loc.gov/METS/}FLocat":
                            fileLocation = item3.get("{http://www.w3.org/1999/xlink}href")
                            fileFullPath = os.path.join(relativeDirectory, fileLocation)
                            dest = os.path.join(transferDirectory, DspaceLicenses, os.path.basename(fileLocation))
                            renameAsSudo(fileFullPath, dest)

                            src = fileFullPath.replace(transferDirectory, "%transferDirectory%")
                            dst = dest.replace(transferDirectory, "%transferDirectory%")
                            eventDetail = ""
                            eventOutcomeDetailNote = "moved from=\"" + src + "\"; moved to=\"" + dst + "\""
                            updateFileLocation(src, dst, "movement", date, eventDetail, transferUUID=transferUUID, eventOutcomeDetailNote = eventOutcomeDetailNote)
    return exitCode



if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.moveDspaceLicenseFilesToDSpaceLicenses")

    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]
    transferDirectory = sys.argv[4]
    transferUUID = sys.argv[5]


    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
