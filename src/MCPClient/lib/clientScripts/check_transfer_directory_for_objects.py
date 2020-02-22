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

import scandir


def call(jobs):
    """
    Check the given directory and it's subdirectories for files.
    Returns job status 0 if there are files.
    Returns job status 1 if the directories are empty.
    """
    for job in jobs:
        with job.JobContext():
            objects_dir = job.args[1]
            os.path.isdir(objects_dir)
            for _, _, files in scandir.walk(objects_dir):
                if files:
                    return
            job.set_status(1)
