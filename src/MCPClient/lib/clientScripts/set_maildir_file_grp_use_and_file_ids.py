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
import os

import django
from custom_handlers import get_script_logger

django.setup()
from django.db import connection
from django.db import transaction
from main.models import File
from main.models import FileFormatVersion
from main.models import FileID

logger = get_script_logger("archivematica.mcp.client.setMaildirFileGrpUseAndFileIDs")


def get_files(sip_uuid, current_location, removed_time=0):
    return File.objects.filter(
        uuid=sip_uuid, current_location=current_location, removedtime=removed_time
    )


def insert_file_format_version(file_uuid, description):
    sql = f"""
        INSERT INTO {FileFormatVersion._meta.db_table} (fileUUID, fileID)
        VALUES (%s, (
            SELECT pk
            FROM {FileID._meta.db_table}
            WHERE
                enabled = TRUE
                AND description = %s
            ));
    """
    with connection.cursor() as cursor:
        return cursor.execute(sql, [file_uuid, description])


def set_maildir_files(sip_uuid, sip_path):
    maildir_path = os.path.join(sip_path, "objects", "Maildir")
    logger.info(
        "Walking the Maildir tree (maildir_path=%s, sip_uuid=%s) to populate FileFormatVersion data",
        maildir_path,
        sip_uuid,
    )
    for root, _, files in os.walk(maildir_path):
        for item in files:
            file_relative_path = os.path.join(root, item).replace(
                sip_path, "%SIPDirectory%", 1
            )
            files = get_files(sip_uuid, file_relative_path)
            if not files.count():
                continue
            insert_file_format_version(
                files[0].uuid, description="A maildir email file"
            )


def set_archivematica_maildir_files(sip_uuid, sip_path):
    attachments_path = os.path.join(sip_path, "objects", "attachments")
    logger.info(
        "Walking the attachments directory (attachments_path=%s, sip_uuid=%s) to populate FileFormatVersion data",
        attachments_path,
        sip_uuid,
    )
    for root, _, files in os.walk(attachments_path):
        for item in files:
            if not item.endswith(".archivematicaMaildir"):
                continue
            file_relative_path = os.path.join(root, item).replace(
                sip_path, "%SIPDirectory%", 1
            )
            files = get_files(sip_uuid, file_relative_path)
            if not files.count():
                continue
            insert_file_format_version(
                files[0].uuid, description="A .archivematicaMaildir file"
            )


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                sip_uuid = job.args[1]
                sip_path = job.args[2]

                set_maildir_files(sip_uuid, sip_path)
                set_archivematica_maildir_files(sip_uuid, sip_path)
