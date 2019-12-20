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

import lxml.etree as etree
import os
import tempfile

# archivematicaCommon
from archivematicaFunctions import getTagged
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoFPCommandOutput
from executeOrRunSubProcess import executeOrRun

import django
from django.db import transaction

django.setup()
# dashboard
from main.models import FPCommandOutput


logger = get_script_logger("archivematica.mcp.client.FITS")

formats = []
FITSNS = "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}"


def exclude_jhove_properties(fits):
    """
    Exclude <properties> from "/fits/toolOutput/tool[name=Jhove]/repInfo"
    because that field contains unnecessary excess data and the key data are
    covered by output from other FITS tools.
    """
    format_validation = None
    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Jhove":
            format_validation = tool
            break
    if format_validation is None:
        return fits
    repInfo = getTagged(format_validation, "repInfo")[0]
    properties = getTagged(repInfo, "properties")
    if len(properties):
        repInfo.remove(properties[0])
    return fits


def main(target, xml_file, date, event_uuid, file_uuid, file_grpuse):
    """
    Note: xml_file, date and event_uuid are not being used.
    """
    if file_grpuse in ("DSPACEMETS", "maildirFile"):
        logger.error("File's fileGrpUse in exclusion list, skipping")
        return 0

    if not FPCommandOutput.objects.filter(file=file_uuid).exists():
        logger.error("Warning: Fits has already run on this file. Not running again.")
        return 0

    _, temp_file = tempfile.mkstemp()
    args = ["fits.sh", "-i", target, "-o", temp_file]
    try:
        logger.info("Executing %s", args)
        retcode, stdout, stderr = executeOrRun(
            "command", args, printing=False, capture_output=True
        )

        if retcode != 0:
            logger.error(
                "fits.sh exited with status code %s, %s, %s", retcode, stdout, stderr
            )
            return retcode

        try:
            tree = etree.parse(temp_file)
        except:
            logger.exception("Failed to read Fits's XML.")
            return 2

        fits = tree.getroot()
        fits = exclude_jhove_properties(fits)

        # NOTE: This is hardcoded for now because FPCommandOutput references FPRule for future development,
        #       when characterization will become user-configurable and be decoupled from FITS specifically.
        #       Thus a stub rule must exist for FITS; this will be replaced with a real rule in the future.
        logger.info("Storing output of file characterization...")
        insertIntoFPCommandOutput(
            file_uuid,
            etree.tostring(fits, pretty_print=False),
            "3a19de70-0e42-4145-976b-3a248d43b462",
        )

    except (OSError, ValueError):
        logger.exception("Execution failed")
        return 1

    finally:
        # We are responsible for removing the temporary file and we do it here
        # to ensure that it's going to happen whatever occurs inside our try
        # block.
        os.remove(temp_file)

    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = job.args[1:]
                job.set_status(main(*args))
