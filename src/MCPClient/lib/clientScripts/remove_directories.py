#!/usr/bin/env python

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

import os
import shutil


def call(jobs):
    for job in jobs:
        with job.JobContext():
            for directory in job.args[1:]:
                if os.path.isdir(directory):
                    job.pyprint("Removing directory:", directory)
                    shutil.rmtree(directory)
                else:
                    job.pyprint("Directory does not exist:", directory)
