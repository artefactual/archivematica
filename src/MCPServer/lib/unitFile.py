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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict


class unitFile(object):
    """For objects representing a File"""
    def __init__(self, currentPath, UUID="None", owningUnit=None):
        self.currentPath = currentPath
        self.UUID = UUID
        self.owningUnit = owningUnit
        self.fileGrpUse = 'None'
        self.fileList = {currentPath: self}
        self.pathString = ""
        if owningUnit:
            self.pathString = owningUnit.pathString

    def getReplacementDic(self, target=None):
        if target is not None and self.owningUnit:
            return self.owningUnit.getReplacementDic(self.owningUnit.currentPath)
        elif self.UUID != "None":
            return ReplacementDict.frommodel(
                type_='file',
                file_=self.UUID
            )
        # If no UUID has been assigned yet, we can't use the
        # ReplacementDict.frommodel constructor; fall back to the
        # old style of manual construction.
        else:
            return {
                "%relativeLocation%": self.currentPath,
                "%fileUUID%": self.UUID,
                "%fileGrpUse%": self.fileGrpUse
            }

    def reload(self):
        pass

    def reloadFileList(self):
        pass
