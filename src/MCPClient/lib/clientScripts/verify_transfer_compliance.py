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
import sys

import scandir

from verify_sip_compliance import checkDirectory

REQUIRED_DIRECTORIES = (
    "objects",
    "logs",
    "metadata",
    "metadata/submissionDocumentation",
)

ALLOWABLE_FILES = ("processingMCP.xml",)


def verifyDirectoriesExist(job, SIPDir, ret=0):
    for directory in REQUIRED_DIRECTORIES:
        if not os.path.isdir(os.path.join(SIPDir, directory)):
            job.pyprint(
                "Required Directory Does Not Exist: " + directory, file=sys.stderr
            )
            ret += 1
    return ret


def verifyNothingElseAtTopLevel(job, SIPDir, ret=0):
    for entry in os.listdir(SIPDir):
        if os.path.isdir(os.path.join(SIPDir, entry)):
            if entry not in REQUIRED_DIRECTORIES:
                job.pyprint("Error, directory exists: " + entry, file=sys.stderr)
                ret += 1
        else:
            if entry not in ALLOWABLE_FILES:
                job.pyprint("Error, file exists: " + entry, file=sys.stderr)
                ret += 1
    return ret


def verifyThereAreFiles(job, SIPDir, ret=0):
    """Make sure there are files in the transfer."""
    if not any(files for (_, _, files) in scandir.walk(SIPDir)):
        job.pyprint("Error, no files found", file=sys.stderr)
        ret += 1
    return ret


def call(jobs):
    for job in jobs:
        with job.JobContext():
            SIPDir = job.args[1]
            ret = verifyDirectoriesExist(job, SIPDir)
            ret = verifyNothingElseAtTopLevel(job, SIPDir, ret)
            ret = checkDirectory(job, SIPDir, ret)
            ret = verifyThereAreFiles(job, SIPDir, ret)
            if ret != 0:
                import time

                time.sleep(10)
            job.set_status(ret)
