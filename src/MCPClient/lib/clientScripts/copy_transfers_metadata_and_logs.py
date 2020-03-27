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
import shutil
from optparse import OptionParser
import traceback

import django

django.setup()

from bag import is_bag
from main.models import File, SIP

from archivematicaFunctions import find_transfer_path_from_ingest


def main(
    job, sipUUID, transfersMetadataDirectory, transfersLogsDirectory, sharedPath=""
):
    if not os.path.exists(transfersMetadataDirectory):
        os.makedirs(transfersMetadataDirectory)
    if not os.path.exists(transfersLogsDirectory):
        os.makedirs(transfersLogsDirectory)

    exitCode = 0

    sip = SIP.objects.get(uuid=sipUUID)
    transfer_paths = (
        File.objects.filter(sip_id=sipUUID, transfer__isnull=False)
        .order_by("transfer__uuid")
        .values_list("transfer__currentlocation", flat=True)
        .distinct()
    )
    for transferPath in transfer_paths:
        try:
            transferPath = find_transfer_path_from_ingest(transferPath, sharedPath)
            job.pyprint("Transfer found in", transferPath)

            if is_bag(transferPath):
                transfer_logs_dir = os.path.join(transferPath, "data", "logs")
                transfer_md_dir = os.path.join(transferPath, "data", "metadata")
            else:
                transfer_logs_dir = os.path.join(transferPath, "logs")
                transfer_md_dir = os.path.join(transferPath, "metadata")

            transferBasename = os.path.basename(os.path.abspath(transferPath))

            # Copy transfer metadata
            if "REIN" in sip.sip_type:
                # For reingest, ignore this transfer's metadata, only copy metadata from the original Transfer
                transferMetaDestDir = transfersMetadataDirectory
                transferMetadataDirectory = os.path.join(
                    transferPath, "metadata", "transfers"
                )
            else:
                transferMetaDestDir = os.path.join(
                    transfersMetadataDirectory, transferBasename
                )
                os.makedirs(transferMetaDestDir)
                transferMetadataDirectory = transfer_md_dir
            if not os.path.exists(transferMetadataDirectory):
                continue
            for met in os.listdir(transferMetadataDirectory):
                if met == "submissionDocumentation":
                    continue
                src = os.path.join(transferMetadataDirectory, met)
                dst = os.path.join(transferMetaDestDir, met)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy(src, dst)
                job.pyprint("copied: ", src, " -> ", dst)

            # Copy transfer logs
            transfersLogsDestDir = os.path.join(
                transfersLogsDirectory, transferBasename
            )
            os.makedirs(transfersLogsDestDir)
            src = transfer_logs_dir
            dst = os.path.join(transfersLogsDestDir, "logs")
            shutil.copytree(src, dst)
            job.pyprint("copied: ", src, " -> ", dst)

        except Exception:
            job.print_error(traceback.format_exc())
            exitCode += 1

    return exitCode


def call(jobs):
    parser = OptionParser()
    parser.add_option(
        "-s", "--sipDirectory", action="store", dest="sipDirectory", default=""
    )
    parser.add_option("-S", "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option(
        "-p",
        "--sharedPath",
        action="store",
        dest="sharedPath",
        default="/var/archivematica/sharedDirectory/",
    )

    for job in jobs:
        with job.JobContext():
            (opts, args) = parser.parse_args(job.args[1:])

            job.set_status(
                main(
                    job,
                    opts.sipUUID,
                    opts.sipDirectory + "metadata/transfers/",
                    opts.sipDirectory + "logs/transfers/",
                    sharedPath=opts.sharedPath,
                )
            )
