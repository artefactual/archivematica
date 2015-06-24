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
from __future__ import print_function
import sys
import os

SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]

manualNormalizationPath = os.path.join(SIPDirectory, "objects", "manualNormalization")
print('Manual normalization path:', manualNormalizationPath)
if os.path.isdir(manualNormalizationPath):
    mn_access_path = os.path.join(manualNormalizationPath, "access")
    mn_preserve_path = os.path.join(manualNormalizationPath, "preservation")
    # Return to indicate manually normalized files exist
    if os.path.isdir(mn_access_path) and os.listdir(mn_access_path):
        print('Manually normalized files found')
        sys.exit(179)

    if os.path.isdir(mn_preserve_path) and os.listdir(mn_preserve_path):
        print('Manually normalized files found')
        sys.exit(179)
exit(0)
