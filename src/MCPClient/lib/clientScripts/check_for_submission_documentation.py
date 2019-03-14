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


def call(jobs):
    for job in jobs:
        with job.JobContext():
            target = job.args[1]
            if not os.path.isdir(target):
                job.pyprint("Directory doesn't exist: ", target, file=sys.stderr)
                os.mkdir(target)
            if os.listdir(target) == []:
                job.pyprint("Directory is empty: ", target, file=sys.stderr)
                fileName = os.path.join(target, "submissionDocumentation.log")
                f = open(fileName, "a")
                f.write("No submission documentation added")
                f.close()
                os.chmod(fileName, 488)
