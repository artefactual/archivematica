#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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

"""Handle Unstored DIP.

This client script hanles an unstored DIP by moving it to the rejected/
directory if it has *not* been uploaded and doing nothing otherwise.
"""

import os
import shutil

import django

django.setup()
from django.db import transaction

# archivematicaCommon
from custom_handlers import get_script_logger


logger = get_script_logger("archivematica.mcp.client.handleUnstoredDIP")


def _get_sip_dirname(sip_path):
    return os.path.basename(sip_path.rstrip("/"))


def _sip_uploaded(sip_path, uploaded_dips_path):
    """Return ``True`` if the SIP has been uploaded."""
    return os.path.isdir(os.path.join(uploaded_dips_path, _get_sip_dirname(sip_path)))


def _move_to_rejected(sip_path, rejected_path):
    """Move the SIP at ``sip_path`` to the rejected directory at
    ``rejected_path``.
    """
    dest = os.path.join(rejected_path, _get_sip_dirname(sip_path))
    shutil.move(sip_path, dest)
    return dest


def main(job, sip_path, rejected_path, uploaded_dips_path):
    if _sip_uploaded(sip_path, uploaded_dips_path):
        msg = (
            "The SIP has been uploaded so it was NOT moved to the"
            " rejected/ directory"
        )
    else:
        dest = _move_to_rejected(sip_path, rejected_path)
        msg = (
            "The SIP had NOT been uploaded so it was moved to the"
            " rejected/ directory at %s" % dest
        )
    job.pyprint(msg)
    logger.info(msg)
    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                sip_path, rejected_path, uploaded_dips_path = job.args[1:]
                logger.info(
                    "handleUnstoredDIP called with sip directory %s and rejected"
                    " directory %s",
                    sip_path,
                    rejected_path,
                )
                job.set_status(main(job, sip_path, rejected_path, uploaded_dips_path))
