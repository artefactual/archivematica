#!/usr/bin/python -OO

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
import shutil
# archivematicaCommon
import archivematicaFunctions

if __name__ == '__main__':
    path = sys.argv[1]
    os.makedirs(os.path.join(path, "metadata/submissionDocumentation"))

    # Move everything to submission documentation
    for item in os.listdir(path):
        if item in archivematicaFunctions.OPTIONAL_FILES + ["metadata"]:
            continue
        src = os.path.join(path, item)
        dst = os.path.join(path, "metadata/submissionDocumentation", item)
        print 'Moving', src, 'to', dst
        shutil.move(src, dst)
    src = os.path.join(path, "metadata/submissionDocumentation", "data/objects")
    dst = path
    if os.path.exists(src):
        print 'Moving', src, 'to', dst
        shutil.move(src, dst)

    archivematicaFunctions.create_structured_directory(path, manual_normalization=True, printing=True)
