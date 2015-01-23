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
# archivematicaCommon
from fileOperations import renameAsSudo

# dashboard
from main.models import Transfer

def updateDB(dst, transferUUID):
    Transfer.objects.filter(uuid=transferUUID).update(currentlocation=dst)

def moveSIP(src, dst, transferUUID, sharedDirectoryPath):
    # os.rename(src, dst)
    if src.endswith("/"):
        src = src[:-1]

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))
    updateDB(dest + "/", transferUUID)

    renameAsSudo(src, dst)

if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2]
    transferUUID = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    moveSIP(src, dst, transferUUID, sharedDirectoryPath)
