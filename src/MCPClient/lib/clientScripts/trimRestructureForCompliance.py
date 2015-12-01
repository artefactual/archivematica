#!/usr/bin/env python2

import os
import sys

# fileOperations requires Django to be set up
import django
django.setup()
# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES
from custom_handlers import get_script_logger
import fileOperations

def restructureTRIMForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType="transfer_id", unitPathReplaceWith="%transferDirectory%"):
    # Create required directories
    archivematicaFunctions.create_directories(REQUIRED_DIRECTORIES, unitPath)

    # The types returned by os.listdir() depends on the type of the argument
    # passed to it. In this case, we want all of the returned names to be
    # bytestrings because they may contain arbitrary, non-Unicode characters.
    unitPath = str(unitPath)
    for item in os.listdir(unitPath):
        if item in REQUIRED_DIRECTORIES:
            continue
        src = os.path.join(unitPath, item)
        if os.path.isdir(src):
            objectsDir = os.path.join(unitPath, "objects", item)
            os.mkdir(objectsDir)
            for item2 in os.listdir(src):
                itemPath = os.path.join(src, item2)
                dst = os.path.join(objectsDir, item2)
                fileOperations.updateFileLocation2(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)

                if item2.endswith("Metadata.xml"):
                    TRIMfileID = os.path.join(item, item2[:-1 - len("Metadata.xml")])
                    files = fileOperations.getFileUUIDLike('%' + TRIMfileID + '%', unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
                    fileUUID = None
                    fileGrpUUID = None
                    for key, value in files.iteritems():
                        if key.endswith("Metadata.xml"):
                            fileUUID = value
                        else:
                            fileGrpUUID = value
                    if fileUUID and fileGrpUUID:
                        fileGrpUse = "TRIM file metadata"
                        fileOperations.updateFileGrpUsefileGrpUUID(fileUUID, fileGrpUse, fileGrpUUID)
                    elif fileUUID and not fileGrpUUID:
                        fileOperations.updateFileGrpUse(fileUUID, "TRIM container metadata")
            os.removedirs(src)
        else:
            destDir = "metadata"
            if item == "manifest.txt":
                destDir = "metadata/submissionDocumentation"
            dst = os.path.join(unitPath, destDir, item)
            fileOperations.updateFileLocation2(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
            files = fileOperations.getFileUUIDLike(dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
            for key, value in files.iteritems():
                fileUUID = value
                fileOperations.updateFileGrpUse(fileUUID, "TRIM metadata")

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.trimRestructureForCompliance")

    transferUUID = sys.argv[1]
    transferName = sys.argv[2]
    transferPath = sys.argv[3]
    restructureTRIMForComplianceFileUUIDsAssigned(transferPath, transferUUID)
