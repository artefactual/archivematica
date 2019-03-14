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
from lxml import etree as etree
import sys
import uuid

# fileOperations, databaseFunctions requires Django to be set up
import django

django.setup()
from django.db import transaction

# archivematicaCommon
from archivematicaFunctions import get_file_checksum
from fileOperations import getFileUUIDLike
import databaseFunctions


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                # job.args[2] (transferName) is unused.
                transferUUID = job.args[1]
                transferPath = job.args[3]
                date = job.args[4]
                exitCode = 0

                for transfer_dir in os.listdir(transferPath):
                    dirPath = os.path.join(transferPath, transfer_dir)
                    if not os.path.isdir(dirPath):
                        continue
                    for transfer_file in os.listdir(dirPath):
                        filePath = os.path.join(dirPath, transfer_file)
                        if (
                            transfer_file == "ContainerMetadata.xml"
                            or transfer_file.endswith("Metadata.xml")
                            or not os.path.isfile(filePath)
                        ):
                            continue

                        i = transfer_file.rfind(".")
                        if i != -1:
                            xmlFile = transfer_file[:i] + "_Metadata.xml"
                        else:
                            xmlFile = transfer_file + "_Metadata.xml"
                        xmlFilePath = os.path.join(dirPath, xmlFile)
                        try:
                            tree = etree.parse(xmlFilePath)
                            root = tree.getroot()

                            xmlMD5 = root.find("Document/MD5").text
                        except:
                            job.pyprint("Error parsing: ", xmlFilePath, file=sys.stderr)
                            exitCode += 1
                            continue

                        objectMD5 = get_file_checksum(filePath, "md5")

                        if objectMD5 == xmlMD5:
                            job.pyprint(
                                "File OK: ",
                                xmlMD5,
                                filePath.replace(transferPath, "%TransferDirectory%"),
                            )

                            fileID = getFileUUIDLike(
                                filePath,
                                transferPath,
                                transferUUID,
                                "transfer",
                                "%transferDirectory%",
                            )
                            for path, fileUUID in fileID.items():
                                eventDetail = 'program="python"; module="hashlib.md5()"'
                                eventOutcome = "Pass"
                                eventOutcomeDetailNote = "%s %s" % (
                                    xmlFile.__str__(),
                                    "verified",
                                )
                                eventIdentifierUUID = uuid.uuid4().__str__()

                                databaseFunctions.insertIntoEvents(
                                    fileUUID=fileUUID,
                                    eventIdentifierUUID=eventIdentifierUUID,
                                    eventType="fixity check",
                                    eventDateTime=date,
                                    eventOutcome=eventOutcome,
                                    eventOutcomeDetailNote=eventOutcomeDetailNote,
                                    eventDetail=eventDetail,
                                )
                        else:
                            job.pyprint(
                                "Checksum mismatch: ",
                                filePath.replace(transferPath, "%TransferDirectory%"),
                                file=sys.stderr,
                            )
                            exitCode += 1

                job.set_status(exitCode)
