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

import uuid
import shutil
import os
import sys

import django
from django.db import transaction

django.setup()
# dashboard
from main.models import File

# archivematicaCommon
import archivematicaFunctions
import databaseFunctions


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                objectsDirectory = job.args[1]
                transferName = job.args[2]
                transferUUID = job.args[3]
                processingDirectory = job.args[4]
                autoProcessSIPDirectory = job.args[5]
                sharedPath = job.argv[6]
                transfer_objects_directory = "%transferDirectory%objects"

                for container in os.listdir(objectsDirectory):
                    sipUUID = uuid.uuid4().__str__()
                    containerPath = os.path.join(objectsDirectory, container)
                    if not os.path.isdir(containerPath):
                        job.pyprint(
                            "file (not container) found: ", container, file=sys.stderr
                        )
                        continue

                    sipName = "%s-%s" % (transferName, container)

                    tmpSIPDir = os.path.join(processingDirectory, sipName) + "/"
                    destSIPDir = os.path.join(autoProcessSIPDirectory, sipName) + "/"
                    archivematicaFunctions.create_structured_directory(
                        tmpSIPDir, manual_normalization=True
                    )
                    databaseFunctions.createSIP(
                        destSIPDir.replace(sharedPath, "%sharedPath%"),
                        sipUUID,
                        printfn=job.pyprint,
                    )

                    # move the objects to the SIPDir
                    for item in os.listdir(containerPath):
                        shutil.move(
                            os.path.join(containerPath, item),
                            os.path.join(tmpSIPDir, "objects", item),
                        )

                    # get the database list of files in the objects directory
                    # for each file, confirm it's in the SIP objects directory, and update the current location/ owning SIP'
                    directory = os.path.join(transfer_objects_directory, container)
                    files = File.objects.filter(
                        removedtime__isnull=True,
                        currentlocation__startswith=directory,
                        transfer_id=transferUUID,
                    )
                    for f in files:
                        currentPath = databaseFunctions.deUnicode(
                            f.currentlocation
                        ).replace(directory, transfer_objects_directory)
                        currentSIPFilePath = currentPath.replace(
                            "%transferDirectory%", tmpSIPDir
                        )
                        if os.path.isfile(currentSIPFilePath):
                            f.currentlocation = currentPath.replace(
                                "%transferDirectory%", "%SIPDirectory%"
                            )
                            f.sip_id = sipUUID
                            f.save()
                        else:
                            job.pyprint(
                                "file not found: ", currentSIPFilePath, file=sys.stderr
                            )

                    # moveSIPTo autoProcessSIPDirectory
                    shutil.move(tmpSIPDir, destSIPDir)
