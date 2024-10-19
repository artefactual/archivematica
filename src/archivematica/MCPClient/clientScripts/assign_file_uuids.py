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
"""Assign a UUID to each file in the target directory.

This client script assigns a UUID to a file by generating a new UUID and
creating several database rows (model instances), among them a ``File``
instance recording the UUID associated to a unit model, i.e., to a ``Transfer``
or ``SIP`` instance. ``Event`` instances are also created for "ingestion" and
"accession" events.

Salient parameters are the UUID of the containing unit (Transfer or SIP), the
path to the SIP directory, and the subdirectory being targeted if any.

"""

import argparse
import os
import uuid

import django
from django.db import transaction

django.setup()

import metsrw
import namespaces as ns
from archivematicaFunctions import chunk_iterable
from archivematicaFunctions import find_mets_file
from custom_handlers import get_script_logger
from fileOperations import addFileToSIP
from fileOperations import addFileToTransfer
from main.models import File
from main.models import Transfer

logger = get_script_logger("archivematica.mcp.client.assignFileUUID")

TRANSFER = "Transfer"
SIP = "SIP"


def get_file_info_from_mets(job, mets, file_path_relative_to_sip):
    """
    Look up information about the file in the METS document using metsrw.

    :return: Dict with info. Keys: 'uuid', 'filegrpuse'
    """
    current_path = file_path_relative_to_sip

    file_path_relative_to_sip = file_path_relative_to_sip.replace(
        "%transferDirectory%", "", 1
    ).replace("%SIPDirectory%", "", 1)

    # Warning! This is not the fastest way to achieve this. But we will focus
    # on optimizations later.
    # TODO: is it ok to assume that the file structure is flat?
    # TODO will this work with original vs normalized paths?
    entry = mets.get_file(path=file_path_relative_to_sip)
    if not entry:
        job.print_error(
            f"FSEntry for file {file_path_relative_to_sip} not found in METS"
        )
        return {}
    job.print_output(f"File {entry.path} with UUID {entry.file_uuid} found in METS.")

    # Get original path
    amdsec = entry.amdsecs[0]
    for item in amdsec.subsections:
        if item.subsection == "techMD":
            techmd = item
    pobject = techmd.contents.document  # Element
    original_path = ns.xml_findtext_premis(pobject, "premis:originalName")

    return {
        "uuid": entry.file_uuid,
        "filegrpuse": entry.use,
        "current_path": current_path,
        "original_path": original_path,
    }


def get_transfer_file_queryset(transfer_uuid):
    """Return a queryset for File objects related to the Transfer."""
    return File.objects.filter(transfer=transfer_uuid)


def assign_transfer_file_uuid(
    job,
    filename,
    file_path,
    target_dir,
    mets,
    date="",
    event_uuid=None,
    sip_directory="",
    transfer_uuid=None,
    sip_uuid=None,
    use="original",
    update_use=True,
    filter_subdir=None,
):
    """Walk transaction directory and write files to database.

    If files are in a re-ingested Archivematica AIP, parse the METS
    file and reuse existing information. Otherwise, create a new UUID.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    file_path_relative_to_sip = file_path.replace(
        sip_directory, "%transferDirectory%", 1
    )
    transfer = Transfer.objects.get(uuid=transfer_uuid)
    event_type = "ingestion"
    file_uuid = None

    if transfer.type == Transfer.ARCHIVEMATICA_AIP and mets:
        info = get_file_info_from_mets(job, mets, file_path_relative_to_sip)
        event_type = "reingestion"
        file_uuid = info.get("uuid")
        use = info.get("filegrpuse", use)
        file_path_relative_to_sip = info.get("original_path", file_path_relative_to_sip)

    if not file_uuid:
        file_uuid = str(uuid.uuid4())
        job.print_output(f"Generated UUID for file {file_uuid}")

    addFileToTransfer(
        file_path_relative_to_sip,
        file_uuid,
        transfer_uuid,
        event_uuid,
        date,
        use=use,
        sourceType=event_type,
    )

    # For reingest, the original location was parsed from the METS.
    # Update the current location to reflect what's on disk.
    if transfer.type == Transfer.ARCHIVEMATICA_AIP and mets:
        job.print_output("Updating current location for", file_uuid, "with", info)
        File.objects.filter(uuid=file_uuid).update(
            currentlocation=info["current_path"].encode()
        )


def assign_sip_file_uuid(
    job,
    filename,
    file_path,
    target_dir,
    mets=None,
    date="",
    event_uuid=None,
    sip_directory="",
    transfer_uuid=None,
    sip_uuid=None,
    use="original",
    update_use=True,
    filter_subdir=None,
):
    """Write SIP file to database with new UUID."""
    file_uuid = str(uuid.uuid4())
    file_path_relative_to_sip = file_path.replace(sip_directory, "%SIPDirectory%", 1)

    matching_file = File.objects.filter(
        currentlocation=file_path_relative_to_sip.encode(),
        sip=sip_uuid,
    ).first()
    if matching_file:
        job.print_error(f"File already has UUID: {matching_file.uuid}")
        if update_use:
            matching_file.filegrpuse = use
            matching_file.save()
        return

    job.print_output(f"Generated UUID for file {file_uuid}.")
    addFileToSIP(
        file_path_relative_to_sip,
        file_uuid,
        sip_uuid,
        event_uuid,
        date,
        use=use,
    )


def assign_uuids_to_files_in_dir(**kwargs):
    """Walk target directory and write files to database with new UUID.

    We open a database transaction for each chunk of 10 files, in an
    attempt to balance performance with reasonable transaction lengths.
    """
    target_dir = kwargs["target_dir"]
    transfer_uuid = kwargs["transfer_uuid"]
    for root, _, filenames in os.walk(target_dir):
        for file_chunk in chunk_iterable(filenames):
            with transaction.atomic():
                for filename in file_chunk:
                    if not filename:
                        continue
                    kwargs["filename"] = filename
                    kwargs["file_path"] = os.path.join(root, filename)
                    if transfer_uuid:
                        assign_transfer_file_uuid(**kwargs)
                    else:
                        assign_sip_file_uuid(**kwargs)
    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=uuid.UUID,
        dest="event_uuid",
    )
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument("-S", "--sipUUID", type=uuid.UUID, dest="sip_uuid")
    parser.add_argument("-T", "--transferUUID", type=uuid.UUID, dest="transfer_uuid")
    parser.add_argument("-e", "--use", action="store", dest="use", default="original")
    parser.add_argument(
        "--filterSubdir", action="store", dest="filter_subdir", default=None
    )
    parser.add_argument(
        "--disable-update-filegrpuse",
        action="store_false",
        dest="update_use",
        default=True,
    )

    for job in jobs:
        with job.JobContext(logger=logger):
            kwargs = vars(parser.parse_args(job.args[1:]))
            kwargs["job"] = job

            TRANSFER_SIP_UUIDS = [kwargs["sip_uuid"], kwargs["transfer_uuid"]]
            if all(TRANSFER_SIP_UUIDS) or not any(TRANSFER_SIP_UUIDS):
                job.print_error("SIP exclusive-or Transfer UUID must be defined")
                job.set_status(2)
                return

            mets_file = None
            kwargs["mets"] = None
            try:
                mets_file = find_mets_file(kwargs["sip_directory"])
            except OSError as err:
                job.print_error(f"METS file not found: {err}")
            if mets_file:
                job.print_output(
                    f"Reading METS file {mets_file} for reingested file information."
                )
                kwargs["mets"] = metsrw.METSDocument.fromfile(mets_file)

            kwargs["target_dir"] = kwargs["sip_directory"]
            if kwargs["filter_subdir"]:
                kwargs["target_dir"] = os.path.join(
                    kwargs["sip_directory"], kwargs["filter_subdir"]
                )

            job.set_status(assign_uuids_to_files_in_dir(**kwargs))
