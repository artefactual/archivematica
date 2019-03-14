#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

# fileOperations requires Django to be set up
import django

django.setup()
from django.db import transaction

# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES
import fileOperations


def restructureTRIMForComplianceFileUUIDsAssigned(
    job,
    unitPath,
    unitIdentifier,
    unitIdentifierType="transfer",
    unitPathReplaceWith="%transferDirectory%",
):
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
                fileOperations.updateFileLocation2(
                    itemPath,
                    dst,
                    unitPath,
                    unitIdentifier,
                    unitIdentifierType,
                    unitPathReplaceWith,
                    printfn=job.pyprint,
                )

                if item2.endswith("Metadata.xml"):
                    TRIMfileID = os.path.join(item, item2[: -1 - len("Metadata.xml")])
                    files = fileOperations.getFileUUIDLike(
                        "%" + TRIMfileID + "%",
                        unitPath,
                        unitIdentifier,
                        unitIdentifierType,
                        unitPathReplaceWith,
                    )
                    fileUUID = None
                    fileGrpUUID = None
                    for key, value in files.items():
                        if key.endswith("Metadata.xml"):
                            fileUUID = value
                        else:
                            fileGrpUUID = value
                    if fileUUID and fileGrpUUID:
                        fileGrpUse = "TRIM file metadata"
                        fileOperations.updateFileGrpUsefileGrpUUID(
                            fileUUID, fileGrpUse, fileGrpUUID
                        )
                    elif fileUUID and not fileGrpUUID:
                        fileOperations.updateFileGrpUse(
                            fileUUID, "TRIM container metadata"
                        )
            os.removedirs(src)
        else:
            destDir = "metadata"
            if item == "manifest.txt":
                destDir = "metadata/submissionDocumentation"
            dst = os.path.join(unitPath, destDir, item)
            fileOperations.updateFileLocation2(
                src,
                dst,
                unitPath,
                unitIdentifier,
                unitIdentifierType,
                unitPathReplaceWith,
                printfn=job.pyprint,
            )
            files = fileOperations.getFileUUIDLike(
                dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith
            )
            for key, value in files.items():
                fileUUID = value
                fileOperations.updateFileGrpUse(fileUUID, "TRIM metadata")


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transferUUID = job.args[1]
                # transferName = job.args[2] # unused?
                transferPath = job.args[3]
                try:
                    restructureTRIMForComplianceFileUUIDsAssigned(
                        job, transferPath, transferUUID
                    )
                except fileOperations.UpdateFileLocationFailed as e:
                    job.set_status(e.code)
