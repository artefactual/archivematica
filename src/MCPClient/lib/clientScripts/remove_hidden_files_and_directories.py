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

import sys
import os
import shutil


def removeHiddenFilesFromDirectory(job, dir):
    for item in os.listdir(dir):
        fullPath = os.path.join(dir, item)
        if os.path.isdir(fullPath):
            if item.startswith("."):
                job.pyprint("Removing directory: ", fullPath)
                shutil.rmtree(fullPath)
            else:
                removeHiddenFilesFromDirectory(job, fullPath)
        elif os.path.isfile(fullPath):
            if item.startswith(".") or item.endswith("~"):
                job.pyprint("Removing file: ", fullPath)
                os.remove(fullPath)

        else:
            job.pyprint("Not file or directory: ", fullPath, file=sys.stderr)


def call(jobs):
    for job in jobs:
        with job.JobContext():
            transferDirectory = job.args[1]
            removeHiddenFilesFromDirectory(job, transferDirectory)
