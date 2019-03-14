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

REQUIRED_DIRECTORIES = (
    "logs",
    "logs/fileMeta",
    "metadata",
    "metadata/submissionDocumentation",
    "objects",
    "objects/Maildir",
)

OPTIONAL_FILES = ("processingMCP.xml",)


def restructureMaildirDirectory(job, unitPath):
    for dir in REQUIRED_DIRECTORIES:
        dirPath = os.path.join(unitPath, dir)
        if not os.path.isdir(dirPath):
            os.mkdir(dirPath)
            job.pyprint("creating: ", dir)
    for item in os.listdir(unitPath):
        dst = os.path.join(unitPath, "objects", "Maildir") + "/."
        itemPath = os.path.join(unitPath, item)
        if os.path.isdir(itemPath) and item not in REQUIRED_DIRECTORIES:
            shutil.move(itemPath, dst)
            job.pyprint("moving directory to objects/Maildir: ", item)
        elif os.path.isfile(itemPath) and item not in OPTIONAL_FILES:
            shutil.move(itemPath, dst)
            job.pyprint("moving file to objects/Maildir: ", item)


def call(jobs):
    for job in jobs:
        with job.JobContext():
            target = job.args[1]
            restructureMaildirDirectory(job, target)
