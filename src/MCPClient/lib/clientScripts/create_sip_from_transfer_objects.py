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
import shutil
import os
import sys
import uuid

import django

django.setup()
from django.db import transaction

# dashboard
from main.models import File, Directory, SIP, Transfer, UnitVariable, Agent

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
                sharedPath = job.args[6]
                sipName = transferName

                # tmpSIPDir has a trailing slash
                tmpSIPDir = os.path.join(processingDirectory, sipName, "")
                archivematicaFunctions.create_structured_directory(
                    tmpSIPDir, manual_normalization=False
                )

                # If transfer is a reingested AIP, then pass that info to the SIP
                sip_type = "SIP"
                sip_uuid = None
                transfer = Transfer.objects.get(uuid=transferUUID)
                if transfer.type == "Archivematica AIP":
                    sip_type = "AIP-REIN"
                    # Use reingested AIP's UUID as the SIP UUID
                    # Get AIP UUID from reingest METS name
                    job.pyprint(
                        "path",
                        os.path.join(objectsDirectory, "..", "metadata"),
                        "listdir",
                        os.listdir(os.path.join(objectsDirectory, "..", "metadata")),
                    )
                    for item in os.listdir(
                        os.path.join(objectsDirectory, "..", "metadata")
                    ):
                        if item.startswith("METS"):
                            sip_uuid = item.replace("METS.", "").replace(".xml", "")
                job.pyprint("sip_uuid", sip_uuid)
                job.pyprint("sip_type", sip_type)

                # Find out if any ``Directory`` models were created for the source
                # ``Transfer``. If so, this fact gets recorded in the new ``SIP`` model.
                dir_mdls = Directory.objects.filter(
                    transfer_id=transferUUID,
                    currentlocation__startswith="%transferDirectory%objects",
                )
                diruuids = dir_mdls.count() > 0

                if sip_uuid is None:
                    sip_uuid = str(uuid.uuid4())

                destSIPDir = os.path.join(
                    autoProcessSIPDirectory, "{}-{}".format(sipName, sip_uuid)
                )

                # TODO: it's not clear in which case a SIP would already exist
                # at this point in the workflow.
                # Create row in SIPs table if one doesn't already exist
                lookup_path = destSIPDir.replace(sharedPath, "%sharedPath%") + os.sep
                sip, created = SIP.objects.get_or_create(
                    uuid=sip_uuid,
                    defaults={
                        "currentpath": lookup_path,
                        "sip_type": sip_type,
                        "diruuids": diruuids,
                    },
                )
                if not created:
                    sip.diruuids = diruuids
                    sip.currentpath = lookup_path
                    sip.save()

                # Set activeAgent using the value in Transfer. This ensures
                # that events generated in Ingest can fall to this value in
                # scenarios where the processing config does not require user
                # interfactions, e.g. in the "automated" processing config.
                try:
                    unit_variable = UnitVariable.objects.get(
                        unittype="Transfer",
                        unituuid=transferUUID,
                        variable="activeAgent",
                    )
                except UnitVariable.DoesNotExist:
                    unit_variable = None
                if unit_variable:
                    try:
                        agent = Agent.objects.get(id=unit_variable.variablevalue)
                    except Agent.DoesNotExist:
                        pass
                    else:
                        sip.update_active_agent(agent.userprofile.user_id)

                # Move the objects to the SIPDir
                for item in os.listdir(objectsDirectory):
                    src_path = os.path.join(objectsDirectory, item)
                    dst_path = os.path.join(tmpSIPDir, "objects", item)
                    # If dst_path already exists and is a directory, shutil.move
                    # will move src_path into it rather than overwriting it;
                    # to avoid incorrectly-nested paths, move src_path's contents
                    # into it instead.
                    if os.path.exists(dst_path) and os.path.isdir(src_path):
                        for subitem in os.listdir(src_path):
                            shutil.move(os.path.join(src_path, subitem), dst_path)
                    else:
                        shutil.move(src_path, dst_path)

                # Get the ``Directory`` models representing the subdirectories in the
                # objects/ directory. For each subdirectory, confirm it's in the SIP
                # objects/ directory, and update the current location and owning SIP.
                for dir_mdl in dir_mdls:
                    currentPath = databaseFunctions.deUnicode(dir_mdl.currentlocation)
                    currentSIPDirPath = currentPath.replace(
                        "%transferDirectory%", tmpSIPDir
                    )
                    if os.path.isdir(currentSIPDirPath):
                        dir_mdl.currentlocation = currentPath.replace(
                            "%transferDirectory%", "%SIPDirectory%"
                        )
                        dir_mdl.sip = sip
                        dir_mdl.save()
                    else:
                        job.pyprint(
                            "directory not found: ", currentSIPDirPath, file=sys.stderr
                        )

                # Get the database list of files in the objects directory.
                # For each file, confirm it's in the SIP objects directory, and update the
                # current location/ owning SIP'
                files = File.objects.filter(
                    transfer_id=transferUUID,
                    currentlocation__startswith="%transferDirectory%objects",
                    removedtime__isnull=True,
                )
                for f in files:
                    currentPath = databaseFunctions.deUnicode(f.currentlocation)
                    currentSIPFilePath = currentPath.replace(
                        "%transferDirectory%", tmpSIPDir
                    )
                    if os.path.isfile(currentSIPFilePath):
                        f.currentlocation = currentPath.replace(
                            "%transferDirectory%", "%SIPDirectory%"
                        )
                        f.sip = sip
                        f.save()
                    else:
                        job.pyprint(
                            "file not found: ", currentSIPFilePath, file=sys.stderr
                        )

                archivematicaFunctions.create_directories(
                    archivematicaFunctions.MANUAL_NORMALIZATION_DIRECTORIES,
                    basepath=tmpSIPDir,
                )

                # Copy the JSON metadata file, if present; this contains a
                # serialized copy of DC metadata entered in the dashboard UI
                # during the transfer.
                src = os.path.normpath(
                    os.path.join(objectsDirectory, "..", "metadata", "dc.json")
                )
                dst = os.path.join(tmpSIPDir, "metadata", "dc.json")
                if os.path.exists(src):
                    shutil.copy(src, dst)

                # Copy processingMCP.xml file
                src = os.path.join(
                    os.path.dirname(objectsDirectory[:-1]), "processingMCP.xml"
                )
                dst = os.path.join(tmpSIPDir, "processingMCP.xml")
                shutil.copy(src, dst)

                # moveSIPTo autoProcessSIPDirectory
                shutil.move(tmpSIPDir.rstrip(os.sep), destSIPDir)
