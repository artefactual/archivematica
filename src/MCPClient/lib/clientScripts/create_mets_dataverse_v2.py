#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Archivematica.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

"""Maps Dataverse specific elements into the AIP METS file generated on ingest.
"""

from __future__ import print_function
import sys

import archivematicaFunctions
from custom_handlers import get_script_logger

import metsrw


# Create a module level logger.
logger = get_script_logger("archivematica.mcp.client.createMETSDataverse")


def create_dataverse_sip_dmdsec(job, sip_path):
    """
    Return SIP-level Dataverse dmdSecs for inclusion in the AIP METS.

    :param str sip_path: ...
    :return: List of dmdSec Elements
    """
    logger.info("Create dataverse sip dmdsec %s", sip_path)
    # Retrieve METS.xml from the file system.
    metadata_mets_paths = archivematicaFunctions.find_metadata_files(
        sip_path, "METS.xml", only_transfers=True
    )
    if not metadata_mets_paths:
        return []
    ret = []
    for metadata_path in metadata_mets_paths:
        try:
            mets = metsrw.METSDocument.fromfile(metadata_path)
        except mets.MetsError:
            job.pyprint(
                "Could not parse external METS (Dataverse)",
                metadata_path,
                file=sys.stderr,
            )
            continue
        # Retrieve all directory DMDSecs from the METS.xml.
        for f in mets.all_files():
            if f.type == "Directory" and f.dmdsecs:
                # Serialize
                ret += [d.serialize() for d in f.dmdsecs]
    return ret


def create_dataverse_tabfile_dmdsec(job, sip_path, tabfile):
    """
    Returns dmdSec associated with the given tabfile, if one exists.
    """
    logger.info("Create Dataverse tabfile dmdsec %s", sip_path)
    # Retrieve METS.xml from the file system.
    metadata_mets_paths = archivematicaFunctions.find_metadata_files(
        sip_path, "METS.xml", only_transfers=True
    )
    if not metadata_mets_paths:
        return []
    ret = []
    for metadata_path in metadata_mets_paths:
        try:
            mets = metsrw.METSDocument.fromfile(metadata_path)
        except mets.MetsError:
            job.pyprint(
                "Could not parse external METS (Dataverse)",
                metadata_path,
                file=sys.stderr,
            )
            continue
        # Retrieve all Item DMDSecs from the METS.xml.
        for f in mets.all_files():
            if f.type == "Item" and f.path.endswith(tabfile):
                # Found the correct tabfile
                return [d.serialize() for d in f.dmdsecs]
    return ret
