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
import shutil


# archivematicaCommon
from custom_handlers import get_script_logger
import archivematicaFunctions


logger = get_script_logger("archivematica.mcp.client.restructureBagAIPToSIP")


def _move_file(job, src, dst, exit_on_error=True):
    job.pyprint("Moving", src, "to", dst)
    try:
        shutil.move(src, dst)
    except IOError:
        job.pyprint("Could not move", src)
        if exit_on_error:
            raise


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            try:
                sip_path = job.args[1]

                # Move everything out of data directory
                for item in os.listdir(os.path.join(sip_path, "data")):
                    src = os.path.join(sip_path, "data", item)
                    dst = os.path.join(sip_path, item)
                    _move_file(job, src, dst)

                os.rmdir(os.path.join(sip_path, "data"))

                # Move metadata and logs out of objects if they exist
                objects_path = os.path.join(sip_path, "objects")
                src = os.path.join(objects_path, "metadata")
                dst = os.path.join(sip_path, "metadata")
                _move_file(job, src, dst, exit_on_error=False)

                src = os.path.join(objects_path, "logs")
                dst = os.path.join(sip_path, "logs")
                _move_file(job, src, dst, exit_on_error=False)

                # Move anything unexpected to submission documentation
                # Leave objects, metadata, etc
                # Original METS ends up in submissionDocumentation
                subm_doc_path = os.path.join(
                    sip_path, "metadata", "submissionDocumentation"
                )
                os.makedirs(subm_doc_path)
                mets_file_path = None
                for item in os.listdir(sip_path):
                    # Leave SIP structure
                    if (
                        item
                        in archivematicaFunctions.OPTIONAL_FILES
                        + archivematicaFunctions.REQUIRED_DIRECTORIES
                    ):
                        continue
                    src = os.path.join(sip_path, item)
                    dst = os.path.join(subm_doc_path, item)
                    if item.startswith("METS.") and item.endswith(".xml"):
                        mets_file_path = dst
                    _move_file(job, src, dst)

                # Reconstruct any empty directories documented in the METS file under the
                # logical structMap labelled "Normative Directory Structure"
                if mets_file_path:
                    archivematicaFunctions.reconstruct_empty_directories(
                        mets_file_path, objects_path, logger=logger
                    )
                else:
                    logger.info(
                        "Unable to reconstruct empty directories: no METS file"
                        " could be found in {}".format(sip_path)
                    )

                archivematicaFunctions.create_structured_directory(
                    sip_path,
                    manual_normalization=True,
                    printing=True,
                    printfn=job.pyprint,
                )
            except IOError as err:
                job.print_error(repr(err))
                job.set_status(1)
