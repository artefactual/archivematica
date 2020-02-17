#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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

"""Assign a UUID to the passed-in file.

This client script assigns a UUID to a file by generating a new UUID and
creating several database rows (model instances), among them a ``File``
instance recording the UUID associated to a unit model, i.e., to a ``Transfer``
or ``SIP`` instance. ``Event`` instances are also created for "ingestion" and
"accession" events.

Salient parameters are the UUID of the containing unit (Transfer or SIP) and
the path to the file.

"""

import argparse
import glob
import os
import uuid

from django.db import transaction
import django

django.setup()
# dashboard
from main.models import File, Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import addFileToTransfer
from fileOperations import addFileToSIP

import metsrw
import namespaces as ns

logger = get_script_logger("archivematica.mcp.client.assignFileUUID")


def find_mets_file(unit_path):
    """
    Return the location of the original METS in a Archivematica AIP transfer.
    """
    src = os.path.join(unit_path, "metadata")
    mets_paths = glob.glob(os.path.join(src, "METS.*.xml"))

    if len(mets_paths) == 1:
        return mets_paths[0]
    elif len(mets_paths) == 0:
        raise Exception("No METS file found in %s" % src)
    else:
        raise Exception("Multiple METS files found in %s: %r" % (src, mets_paths))


def get_file_info_from_mets(job, sip_directory, file_path_relative_to_sip):
    """
    Look up information about the file in the METS document using metsrw.

    :return: Dict with info. Keys: 'uuid', 'filegrpuse'
    """
    mets_file = find_mets_file(sip_directory)
    if not mets_file:
        logger.info("Archivematica AIP: METS file not found.")
        return {}
    job.print_output("Reading METS file", mets_file, "for reingested file information.")
    logger.info("Archivematica AIP: reading METS file %s.", mets_file)
    mets = metsrw.METSDocument.fromfile(mets_file)

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
        job.print_output("Could not find", file_path_relative_to_sip, "in METS.")
        logger.info(
            "Archivematica AIP: file UUID has not been found in the METS document: %s",
            file_path_relative_to_sip,
        )
        return {}
    logger.info(
        "Archivematica AIP: file UUID of %s has been found in the METS document (%s).",
        entry.file_uuid,
        entry.path,
    )

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


def main(
    job,
    file_uuid=None,
    file_path="",
    date="",
    event_uuid=None,
    sip_directory="",
    sip_uuid=None,
    transfer_uuid=None,
    use="original",
    update_use=True,
):
    if file_uuid == "None":
        file_uuid = None
    if file_uuid:
        logger.error("File already has UUID: %s", file_uuid)
        if update_use:
            File.objects.filter(uuid=file_uuid).update(filegrpuse=use)
        return 0

    # Stop if both or neither of them are used
    if all([sip_uuid, transfer_uuid]) or not any([sip_uuid, transfer_uuid]):
        logger.error("SIP exclusive-or Transfer UUID must be defined")
        return 2

    # Transfer
    if transfer_uuid:
        file_path_relative_to_sip = file_path.replace(
            sip_directory, "%transferDirectory%", 1
        )
        transfer = Transfer.objects.get(uuid=transfer_uuid)
        event_type = "ingestion"
        # For reingest, parse information from the METS
        if transfer.type == "Archivematica AIP":
            info = get_file_info_from_mets(
                job, sip_directory, file_path_relative_to_sip
            )
            event_type = "reingestion"
            file_uuid = info.get("uuid", file_uuid)
            use = info.get("filegrpuse", use)
            file_path_relative_to_sip = info.get(
                "original_path", file_path_relative_to_sip
            )
        if not file_uuid:
            file_uuid = str(uuid.uuid4())
            logger.info("Generated UUID for this file: %s.", file_uuid)
        addFileToTransfer(
            file_path_relative_to_sip,
            file_uuid,
            transfer_uuid,
            event_uuid,
            date,
            use=use,
            sourceType=event_type,
        )
        # For reingest, the original location was parsed from the METS
        # Update the current location to reflect what's on disk
        if transfer.type == "Archivematica AIP":
            job.print_output("updating current location for", file_uuid, "with", info)
            File.objects.filter(uuid=file_uuid).update(
                currentlocation=info["current_path"]
            )
        return 0

    # Ingest
    if sip_uuid:
        file_uuid = str(uuid.uuid4())
        file_path_relative_to_sip = file_path.replace(
            sip_directory, "%SIPDirectory%", 1
        )
        addFileToSIP(
            file_path_relative_to_sip, file_uuid, sip_uuid, event_uuid, date, use=use
        )
        return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--fileUUID", type=str, dest="file_uuid")
    parser.add_argument(
        "-p", "--filePath", action="store", dest="file_path", default=""
    )
    parser.add_argument("-d", "--date", action="store", dest="date", default="")
    parser.add_argument(
        "-u",
        "--eventIdentifierUUID",
        type=lambda x: str(uuid.UUID(x)),
        dest="event_uuid",
    )
    parser.add_argument(
        "-s", "--sipDirectory", action="store", dest="sip_directory", default=""
    )
    parser.add_argument(
        "-S", "--sipUUID", type=lambda x: str(uuid.UUID(x)), dest="sip_uuid"
    )
    parser.add_argument(
        "-T", "--transferUUID", type=lambda x: str(uuid.UUID(x)), dest="transfer_uuid"
    )
    parser.add_argument("-e", "--use", action="store", dest="use", default="original")
    parser.add_argument(
        "--disable-update-filegrpuse",
        action="store_false",
        dest="update_use",
        default=True,
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = vars(parser.parse_args(job.args[1:]))
                args["job"] = job

                job.set_status(main(**(args)))
