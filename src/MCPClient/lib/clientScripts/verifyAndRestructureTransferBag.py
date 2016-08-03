#!/usr/bin/env python2

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
from __future__ import print_function
import os
import sys

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
from custom_handlers import get_script_logger
import fileOperations
from databaseFunctions import insertIntoEvents

from verifyBAG import verify_bag

exitCode = 0

logger = get_script_logger("archivematica.mcp.client.verifyAndRestructureTransferBag")


def restructureBagForComplianceFileUUIDsAssigned(unitPath, unitIdentifier, unitIdentifierType="transfer_id", unitPathReplaceWith="%transferDirectory%"):
    bagFileDefaultDest = os.path.join(unitPath, "logs", "BagIt")
    REQUIRED_DIRECTORIES.append(bagFileDefaultDest)
    # This needs to be cast to a string since we're calling os.path.join(),
    # and any of the other arguments could contain arbitrary, non-Unicode
    # characters.
    unitPath = str(unitPath)
    unitDataPath = str(os.path.join(unitPath, "data"))
    for dir in REQUIRED_DIRECTORIES:
        dirPath = os.path.join(unitPath, dir)
        dirDataPath = os.path.join(unitPath, "data", dir)
        if os.path.isdir(dirDataPath):
            # move to the top level
            src = dirDataPath
            dst = dirPath
            fileOperations.updateDirectoryLocation(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
            print("moving directory ", dir)
        else:
            if not os.path.isdir(dirPath):
                print("creating: ", dir)
                os.mkdir(dirPath)
    for item in os.listdir(unitPath):
        src = os.path.join(unitPath, item)
        if os.path.isfile(src):
            if item.startswith("manifest"):
                dst = os.path.join(unitPath, "metadata", item)
                fileOperations.updateFileLocation2(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
            elif item in OPTIONAL_FILES:
                print("not moving:", item)
            else:
                dst = os.path.join(bagFileDefaultDest, item)
                fileOperations.updateFileLocation2(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
    for item in os.listdir(unitDataPath):
        itemPath = os.path.join(unitDataPath, item)
        if os.path.isdir(itemPath) and item not in REQUIRED_DIRECTORIES:
            print("moving directory to objects: ", item)
            dst = os.path.join(unitPath, "objects", item)
            fileOperations.updateDirectoryLocation(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
        elif os.path.isfile(itemPath) and item not in OPTIONAL_FILES:
            print("moving file to objects: ", item)
            dst = os.path.join(unitPath, "objects", item)
            fileOperations.updateFileLocation2(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
        elif item in OPTIONAL_FILES:
            dst = os.path.join(unitPath, item)
            fileOperations.updateFileLocation2(itemPath, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith)
    print("removing empty data directory")
    os.rmdir(unitDataPath)


if __name__ == '__main__':
    target = sys.argv[1]
    transferUUID = sys.argv[2]
    exitCode = verify_bag(target)
    if exitCode != 0:
        print("Failed bagit compliance. Not restructuring.", file=sys.stderr)
        sys.exit(exitCode)
    restructureBagForComplianceFileUUIDsAssigned(target, transferUUID)

    files = File.objects.filter(removedtime__isnull=True,
                                transfer_id=transferUUID,
                                currentlocation__startswith="%transferDirectory%objects/").values_list('uuid')
    for uuid, in files:
        insertIntoEvents(fileUUID=uuid,
                         eventType="fixity check",
                         eventDetail="Bagit - verifypayloadmanifests",
                         eventOutcome="Pass")

    sys.exit(exitCode)
