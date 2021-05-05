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

import argparse
import os
import uuid

# fileOperations requires Django to be set up
import django
from django.db import transaction

django.setup()

from main.models import File, FileFormatVersion

from archivematicaFunctions import chunk_iterable, find_mets_file
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoDerivations
from fileOperations import updateSizeAndChecksum

import metsrw

import parse_mets_to_db

logger = get_script_logger("archivematica.mcp.client.updateSizeAndChecksum")

SIP_REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
TRANSFER_REPLACEMENT_PATH_STRING = r"%transferDirectory%"


def get_file_info_from_mets(job, mets, file_):
    """Get file size, checksum & type, and derivation for this file from METS.

    Given an instance of a File, return a dict with keys: file_size,
    checksum and checksum_type, as they are described in the original METS
    document of the transfer. The dict will be empty or missing keys on error.
    """
    fsentry = mets.get_file(file_uuid=file_.uuid)
    if not fsentry:
        job.print_error("FSEntry with UUID {} not found in METS".format(file_.uuid))
        return {}

    # Get the UUID of a preservation derivative, if one exists
    try:
        premis_object = fsentry.get_premis_objects()[0]
    except IndexError:
        job.print_error(
            "PREMIS:OBJECT not found for file {} in METS".format(file_.uuid)
        )
        return {}
    premis_object = fsentry.get_premis_objects()[0]
    related_object_uuid = None
    for relationship in premis_object.relationship:
        if relationship.sub_type != "is source of":
            continue
        event = fsentry.get_premis_event(relationship.related_event_identifier_value)
        if (not event) or (event.type != "normalization"):
            continue
        rel_obj_uuid = relationship.related_object_identifier_value
        related_object_fsentry = mets.get_file(file_uuid=rel_obj_uuid)
        if getattr(related_object_fsentry, "use", None) != "preservation":
            continue
        related_object_uuid = rel_obj_uuid
        break

    premis_object_doc = [
        ss.contents.document
        for ss in fsentry.amdsecs[0].subsections
        if ss.contents.mdtype == metsrw.FSEntry.PREMIS_OBJECT
    ][0]

    return {
        "file_size": premis_object.size,
        "checksum": premis_object.message_digest,
        "checksum_type": premis_object.message_digest_algorithm,
        "derivation": related_object_uuid,
        "format_version": parse_mets_to_db.parse_format_version(job, premis_object_doc),
    }


def _filter_queryset_by_subdir(queryset, replacement_path_string, filter_subdir):
    """Filter queryset by filter_subdir."""
    filter_path = "".join([replacement_path_string, filter_subdir])
    return queryset.filter(currentlocation__startswith=filter_path)


def get_transfer_file_queryset(transfer_uuid, filter_subdir):
    """Return Queryset of files in this transfer."""
    files = File.objects.filter(transfer=transfer_uuid)
    if filter_subdir:
        files = _filter_queryset_by_subdir(
            files, TRANSFER_REPLACEMENT_PATH_STRING, filter_subdir
        )
    return files


def get_sip_file_queryset(sip_uuid, filter_subdir):
    """Return Queryset of files in this SIP."""
    files = File.objects.filter(sip=sip_uuid)
    if filter_subdir:
        files = _filter_queryset_by_subdir(
            files, SIP_REPLACEMENT_PATH_STRING, filter_subdir
        )
    return files


def update_size_and_checksum_for_file(
    job,
    file_,
    mets,
    shared_path,
    sip_directory,
    sip_uuid,
    transfer_uuid,
    date,
    event_uuid,
    filter_subdir,
):
    """Update size and checksum for file in database.

    If file is from Archivematica AIP transfer, try to extract and use
    the size, checksum, and checksum type values from the METS.
    """
    kw = {}
    if transfer_uuid:
        file_path = file_.currentlocation.replace(
            TRANSFER_REPLACEMENT_PATH_STRING, sip_directory
        )
    else:
        file_path = file_.currentlocation.replace(
            SIP_REPLACEMENT_PATH_STRING, sip_directory
        )

    if not os.path.exists(file_path):
        return

    if file_.in_reingested_aip and mets:
        info = get_file_info_from_mets(job, mets, file_)
        kw.update(
            fileSize=info["file_size"],
            checksum=info["checksum"],
            checksumType=info["checksum_type"],
            add_event=False,
        )
        if info.get("derivation"):
            insertIntoDerivations(
                sourceFileUUID=file_.uuid, derivedFileUUID=info["derivation"]
            )
        if info.get("format_version"):
            FileFormatVersion.objects.create(
                file_uuid_id=file_.uuid, format_version=info["format_version"]
            )

    job.print_output("Updating file size and checksum for file {}".format(file_.uuid))
    updateSizeAndChecksum(file_.uuid, file_path, date, event_uuid, **kw)


def update_files(
    job,
    files,
    mets,
    shared_path,
    sip_directory,
    sip_uuid,
    transfer_uuid,
    date,
    event_uuid,
    filter_subdir,
):
    """Update file sizes and checksums for each file in list.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    for file_chunk in chunk_iterable(files):
        with transaction.atomic():
            for file_ in file_chunk:
                if not file_:
                    continue
                update_size_and_checksum_for_file(
                    job,
                    file_,
                    mets,
                    shared_path,
                    sip_directory,
                    sip_uuid,
                    transfer_uuid,
                    date,
                    event_uuid,
                    filter_subdir,
                )

    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sharedPath")
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument(
        "-S", "--sipUUID", type=lambda x: str(uuid.UUID(x)), dest="sip_uuid"
    )
    parser.add_argument(
        "-T", "--transferUUID", type=lambda x: str(uuid.UUID(x)), dest="transfer_uuid"
    )
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "--filterSubdir", action="store", dest="filter_subdir", default=None
    )
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=lambda x: str(uuid.UUID(x)),
        dest="event_uuid",
    )

    for job in jobs:
        with job.JobContext(logger=logger):
            args = parser.parse_args(job.args[1:])

            TRANSFER_SIP_UUIDS = [args.sip_uuid, args.transfer_uuid]
            if all(TRANSFER_SIP_UUIDS) or not any(TRANSFER_SIP_UUIDS):
                job.print_error("SIP exclusive-or Transfer UUID must be defined")
                job.set_status(2)
                return

            files = get_transfer_file_queryset(args.transfer_uuid, args.filter_subdir)
            if args.sip_uuid:
                files = get_sip_file_queryset(args.sip_uuid, args.filter_subdir)

            mets_file = None
            mets = None
            try:
                mets_file = find_mets_file(args.sip_directory)
            except OSError as err:
                job.print_error("METS file not found: {}".format(err))
            if mets_file:
                job.print_output("Reading METS file {}".format(mets_file))
                mets = metsrw.METSDocument.fromfile(mets_file)

            job.set_status(
                update_files(
                    job,
                    files,
                    mets,
                    args.sharedPath,
                    args.sip_directory,
                    args.sip_uuid,
                    args.transfer_uuid,
                    args.date,
                    args.event_uuid,
                    args.filter_subdir,
                )
            )
