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


def call(jobs):
    for job in jobs:
        with job.JobContext():
            # Unused?
            # SIPUUID = job.args[1]
            # SIPName = job.args[2]
            SIPDirectory = job.args[3]

            manualNormalizationPath = os.path.join(
                SIPDirectory, "objects", "manualNormalization"
            )
            job.pyprint("Manual normalization path:", manualNormalizationPath)
            if os.path.isdir(manualNormalizationPath):
                mn_access_path = os.path.join(manualNormalizationPath, "access")
                mn_preserve_path = os.path.join(manualNormalizationPath, "preservation")
                # Return to indicate manually normalized files exist
                if os.path.isdir(mn_access_path) and os.listdir(mn_access_path):
                    job.pyprint("Manually normalized files found")
                    job.set_status(179)
                    continue

                if os.path.isdir(mn_preserve_path) and os.listdir(mn_preserve_path):
                    job.pyprint("Manually normalized files found")
                    job.set_status(179)
                    continue

            job.set_status(0)
