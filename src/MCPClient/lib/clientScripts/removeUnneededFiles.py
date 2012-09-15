#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @version svn: $Id$

import sys
import os
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import removeFileByFileUUID
removeIfFileNameIs = ["Thumbs.db", "Icon", u"Icon\u000D"]

def removableFile(target):
    global eventDetailText
    basename = os.path.basename(target)
    if basename in removeIfFileNameIs:
        eventDetailText = basename + " is noted as a removable file."
        return True
    return False

if __name__ == '__main__':
    target = sys.argv[1]
    fileUUID = sys.argv[2]
    logsDirectory = sys.argv[3]
    date = sys.argv[4]
    eIDValue = sys.argv[5]

    global eventDetailText
    eventDetailText = "fileRemoved"
    if removableFile(target):
        print fileUUID + " -> " + os.path.basename(target)
        os.remove(target)
        removeFileByFileUUID(fileUUID)
