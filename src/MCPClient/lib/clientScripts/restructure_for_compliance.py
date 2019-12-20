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

import os
import re
import shutil

import django

django.setup()
from django.db import transaction
from main.models import Transfer, SIP

# archivematicaCommon
from archivematicaFunctions import (
    create_structured_directory,
    reconstruct_empty_directories,
    REQUIRED_DIRECTORIES,
    OPTIONAL_FILES,
)

from custom_handlers import get_script_logger
import bag


logger = get_script_logger("archivematica.mcp.client.restructureForCompliance")


def _move_file(job, src, dst, exit_on_error=True):
    logger.info("Moving %s to %s", src, dst)
    try:
        shutil.move(src, dst)
    except IOError:
        job.pyprint("Could not move", src)
        if exit_on_error:
            raise


def restructure_transfer(job, unit_path):
    # Create required directories
    create_structured_directory(unit_path, printing=True, printfn=job.pyprint)

    # Move everything else to the objects directory
    for item in os.listdir(unit_path):
        src = os.path.join(unit_path, item)
        dst = os.path.join(unit_path, "objects", ".")
        if os.path.isdir(src) and item not in REQUIRED_DIRECTORIES:
            _move_file(job, src, dst)
        elif os.path.isfile(src) and item not in OPTIONAL_FILES:
            _move_file(job, src, dst)


def restructure_transfer_aip(job, unit_path):
    """
    Restructure a transfer that comes from re-ingesting an Archivematica AIP.
    """
    old_bag = os.path.join(unit_path, "old_bag", "")
    os.makedirs(old_bag)

    # Move everything to old_bag
    for item in os.listdir(unit_path):
        if item == "old_bag":
            continue
        src = os.path.join(unit_path, item)
        _move_file(job, src, old_bag)

    # Create required directories
    # - "/logs" and "/logs/fileMeta"
    # - "/metadata" and "/metadata/submissionDocumentation"
    # - "/objects"
    create_structured_directory(unit_path, printing=True, printfn=job.pyprint)

    # Move /old_bag/data/METS.<UUID>.xml => /metadata/METS.<UUID>.xml
    p = re.compile(r"^METS\..*\.xml$", re.IGNORECASE)
    src = os.path.join(old_bag, "data")
    for item in os.listdir(src):
        m = p.match(item)
        if m:
            break  # Stop trying after the first match
    src = os.path.join(src, m.group())
    dst = os.path.join(unit_path, "metadata")
    mets_file_path = dst
    _move_file(job, src, dst)

    # Move /old_bag/data/objects/metadata/* => /metadata/
    src = os.path.join(old_bag, "data", "objects", "metadata")
    dst = os.path.join(unit_path, "metadata")
    if os.path.isdir(src):
        for item in os.listdir(src):
            item_path = os.path.join(src, item)
            _move_file(job, item_path, dst)
        shutil.rmtree(src)

    # Move /old_bag/data/objects/submissionDocumentation/* => /metadata/submissionDocumentation/
    src = os.path.join(old_bag, "data", "objects", "submissionDocumentation")
    dst = os.path.join(unit_path, "metadata", "submissionDocumentation")
    if os.path.isdir(src):
        for item in os.listdir(src):
            item_path = os.path.join(src, item)
            _move_file(job, item_path, dst)
        shutil.rmtree(src)

    # Move /old_bag/data/objects/* => /objects/
    src = os.path.join(old_bag, "data", "objects")
    objects_path = dst = os.path.join(unit_path, "objects")
    for item in os.listdir(src):
        item_path = os.path.join(src, item)
        _move_file(job, item_path, dst)

    # Move /old_bag/processingMCP.xml => /processingMCP.xml
    src = os.path.join(old_bag, "processingMCP.xml")
    dst = os.path.join(unit_path, "processingMCP.xml")
    if os.path.isfile(src):
        _move_file(job, src, dst)

    # Get rid of old_bag
    shutil.rmtree(old_bag)

    # Reconstruct any empty directories documented in the METS file under the
    # logical structMap labelled "Normative Directory Structure"
    reconstruct_empty_directories(mets_file_path, objects_path, logger=logger)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                try:
                    sip_path = job.args[1]
                    sip_uuid = job.args[2]

                    transfer = None
                    sip = None
                    try:
                        transfer = Transfer.objects.get(uuid=sip_uuid)
                    except Transfer.DoesNotExist:
                        sip = SIP.objects.get(uuid=sip_uuid)

                    if transfer:
                        logger.info("Transfer.type=%s", transfer.type)
                    else:
                        logger.info("SIP.sip_type=%s", sip.sip_type)

                    if transfer and transfer.type == "Archivematica AIP":
                        logger.info("Archivematica AIP detected, verifying bag...")
                        if not bag.is_valid(sip_path, job.pyprint):
                            logger.info("Archivematica AIP: bag verification failed!")
                            job.set_status(1)
                            continue
                        logger.info(
                            "Restructuring transfer (Archivematica AIP re-ingest)..."
                        )
                        restructure_transfer_aip(job, sip_path)
                    else:
                        logger.info("Restructuring transfer...")
                        restructure_transfer(job, sip_path)
                except IOError as err:
                    job.pyprint(repr(err))
                    job.set_status(1)
