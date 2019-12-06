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
import os
import sys

import django
from django.db import transaction

django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
import bag
import fileOperations
from databaseFunctions import insertIntoEvents

from move_or_merge import move_or_merge


def restructureBagForComplianceFileUUIDsAssigned(
    job,
    unitPath,
    unitIdentifier,
    unitIdentifierType="transfer_id",
    unitPathReplaceWith="%transferDirectory%",
):
    bagFileDefaultDest = os.path.join(unitPath, "logs", "BagIt")
    MY_REQUIRED_DIRECTORIES = REQUIRED_DIRECTORIES + (bagFileDefaultDest,)
    # This needs to be cast to a string since we're calling os.path.join(),
    # and any of the other arguments could contain arbitrary, non-Unicode
    # characters.
    unitPath = str(unitPath)
    unitDataPath = str(os.path.join(unitPath, "data"))
    for dir in MY_REQUIRED_DIRECTORIES:
        dirPath = os.path.join(unitPath, dir)
        dirDataPath = os.path.join(unitPath, "data", dir)
        if os.path.isdir(dirDataPath):
            if dir == "metadata" and os.path.isdir(dirPath):
                # We move the existing top-level metadata folder, or merge it
                # with what is currently there, before the next set of
                # directory operations to move everything up a level below.
                job.pyprint(
                    "{}: moving/merging {} to {}".format(dir, dirPath, dirDataPath)
                )
                move_or_merge(dirPath, dirDataPath)

            # move to the top level
            src = dirDataPath
            dst = dirPath
            fileOperations.updateDirectoryLocation(
                src,
                dst,
                unitPath,
                unitIdentifier,
                unitIdentifierType,
                unitPathReplaceWith,
            )
            job.pyprint("moving directory ", dir)

        else:
            if not os.path.isdir(dirPath):
                job.pyprint("creating: ", dir)
                os.makedirs(dirPath)
    for item in os.listdir(unitPath):
        src = os.path.join(unitPath, item)
        if os.path.isfile(src):
            if item.startswith("manifest"):
                dst = os.path.join(unitPath, "metadata", item)
                fileOperations.updateFileLocation2(
                    src,
                    dst,
                    unitPath,
                    unitIdentifier,
                    unitIdentifierType,
                    unitPathReplaceWith,
                    printfn=job.pyprint,
                )
            elif item in OPTIONAL_FILES:
                job.pyprint("not moving:", item)
            else:
                dst = os.path.join(bagFileDefaultDest, item)
                fileOperations.updateFileLocation2(
                    src,
                    dst,
                    unitPath,
                    unitIdentifier,
                    unitIdentifierType,
                    unitPathReplaceWith,
                    printfn=job.pyprint,
                )
    for item in os.listdir(unitDataPath):
        itemPath = os.path.join(unitDataPath, item)
        if os.path.isdir(itemPath) and item not in MY_REQUIRED_DIRECTORIES:
            job.pyprint("moving directory to objects: ", item)
            dst = os.path.join(unitPath, "objects", item)
            fileOperations.updateDirectoryLocation(
                itemPath,
                dst,
                unitPath,
                unitIdentifier,
                unitIdentifierType,
                unitPathReplaceWith,
            )
        elif os.path.isfile(itemPath) and item not in OPTIONAL_FILES:
            job.pyprint("moving file to objects: ", item)
            dst = os.path.join(unitPath, "objects", item)
            fileOperations.updateFileLocation2(
                itemPath,
                dst,
                unitPath,
                unitIdentifier,
                unitIdentifierType,
                unitPathReplaceWith,
                printfn=job.pyprint,
            )
        elif item in OPTIONAL_FILES:
            dst = os.path.join(unitPath, item)
            fileOperations.updateFileLocation2(
                itemPath,
                dst,
                unitPath,
                unitIdentifier,
                unitIdentifierType,
                unitPathReplaceWith,
                printfn=job.pyprint,
            )
    job.pyprint("removing empty data directory")
    os.rmdir(unitDataPath)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                target = job.args[1]
                transferUUID = job.args[2]
                if not bag.is_valid(target, printfn=job.pyprint):
                    job.pyprint(
                        "Failed bagit compliance. Not restructuring.", file=sys.stderr
                    )
                    job.set_status(1)
                else:
                    try:
                        restructureBagForComplianceFileUUIDsAssigned(
                            job, target, transferUUID
                        )
                    except fileOperations.UpdateFileLocationFailed as e:
                        job.set_status(e.code)
                        continue

                    files = File.objects.filter(
                        removedtime__isnull=True,
                        transfer_id=transferUUID,
                        currentlocation__startswith="%transferDirectory%objects/",
                    ).values_list("uuid")
                    for (uuid,) in files:
                        insertIntoEvents(
                            fileUUID=uuid,
                            eventType="fixity check",
                            eventDetail="Bagit - verifypayloadmanifests",
                            eventOutcome="Pass",
                        )
