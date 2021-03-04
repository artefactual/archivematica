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

import datetime
import os

import django

django.setup()
from django.db import transaction

# dashboard
from main import models

# archivematicaCommon
from custom_handlers import get_script_logger


logger = get_script_logger("archivematica.mcp.client.storeFileModificationDates")


def get_modification_date(file_path):
    mod_time = os.path.getmtime(file_path)
    return datetime.datetime.utcfromtimestamp(int(mod_time))


def main(transfer_uuid, shared_directory_path):
    transfer = models.Transfer.objects.get(uuid=transfer_uuid)

    files = models.File.objects.filter(transfer=transfer)
    mods_stored = 0
    for transfer_file in files:
        try:
            file_path_relative_to_shared_directory = (
                transfer_file.currentlocation.replace(
                    "%transferDirectory%", transfer.currentlocation, 1
                )
            )
        except AttributeError:
            logger.info(
                "No modification date stored for file %s because it has no current location. It was probably a deleted compressed package.",
                transfer_file.uuid,
            )
        else:
            file_path = file_path_relative_to_shared_directory.replace(
                "%sharedPath%", shared_directory_path, 1
            )
            transfer_file.modificationtime = get_modification_date(file_path)
            transfer_file.save()
            mods_stored += 1

    logger.info("Stored modification dates of %d files.", mods_stored)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                transfer_uuid = job.args[1]
                shared_directory_path = job.args[2]
                main(transfer_uuid, shared_directory_path)
                job.set_status(0)
