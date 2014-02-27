#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES
import fileOperations

def restructureTRIMForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith = "%transferDirectory%"):
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
    transferUUID = sys.argv[1]
    transferName = sys.argv[2]
    transferPath = sys.argv[3]
    restructureTRIMForComplianceFileUUIDsAssigned(transferPath, transferUUID, "transferUUID")
