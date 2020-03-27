#!/usr/bin/env python

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
from __future__ import absolute_import
import os
import re
import shutil

import django

django.setup()

from bag import is_bag
from main.models import File, SIP

from archivematicaFunctions import find_transfer_path_from_ingest


def call(jobs):
    for job in jobs:
        with job.JobContext():
            sipUUID = job.args[1]
            submissionDocumentationDirectory = job.args[2]
            sharedPath = job.args[3]

            transfer_locations = (
                File.objects.filter(
                    removedtime__isnull=True,
                    sip_id=sipUUID,
                    transfer__currentlocation__isnull=False,
                )
                .values_list("transfer__currentlocation", flat=True)
                .distinct()
            )

            sip = SIP.objects.get(uuid=sipUUID)
            aip_mets_name = "METS." + sipUUID + ".xml"

            for transferLocation in transfer_locations:
                transferNameUUID = os.path.basename(os.path.abspath(transferLocation))
                transferLocation = find_transfer_path_from_ingest(
                    transferLocation, sharedPath
                )
                job.pyprint("Transfer found in", transferLocation)

                src = os.path.join(
                    transferLocation, "metadata", "submissionDocumentation"
                )
                dst = os.path.join(
                    submissionDocumentationDirectory, "transfer-%s" % (transferNameUUID)
                )

                # For reingest, ignore this transfer's submission docs, only copy submission docs from the original Transfer
                if "REIN" in sip.sip_type:
                    # Copy original AIP's METS if it exists. There should only ever be one of these in all source transfers.
                    aip_src = os.path.join(transferLocation, "metadata", aip_mets_name)
                    aip_dst = os.path.join(
                        submissionDocumentationDirectory, aip_mets_name
                    )
                    shutil.copy(aip_src, aip_dst)
                    job.pyprint(
                        "copied original AIP METS to submissionDocumentation: ",
                        aip_src,
                        " -> ",
                        aip_dst,
                    )

                    # Only copy previous transfers and old AIP METS
                    for item in os.listdir(src):
                        if re.match(
                            r"^transfer-.+-[\w]{8}(-[\w]{4}){3}-[\w]{12}$", item
                        ):
                            item_path = os.path.join(src, item)
                            dst = os.path.join(submissionDocumentationDirectory, item)
                            job.pyprint(item_path, " -> ", dst)
                            shutil.copytree(item_path, dst)
                else:
                    if is_bag(transferLocation):
                        src = os.path.join(
                            transferLocation,
                            "data",
                            "metadata",
                            "submissionDocumentation",
                        )
                    job.pyprint(src, " -> ", dst)
                    shutil.copytree(src, dst)
