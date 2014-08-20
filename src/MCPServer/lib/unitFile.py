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

class unitFile(object):
    """For objects representing a File"""
    def __init__(self, currentPath, UUID="None", owningUnit=None):
        self.currentPath = currentPath
        self.UUID = UUID
        self.owningUnit = owningUnit
        self.fileGrpUse = 'None'
        self.fileList={currentPath:self}
        self.pathString = ""
        if owningUnit:
            self.pathString = owningUnit.pathString

    def getReplacementDic(self, target=None):
        if target != None and self.owningUnit:
            return self.owningUnit.getReplacementDic(self.owningUnit.currentPath)
        # self.currentPath = currentPath.__str__()
        # self.UUID = uuid.uuid4().__str__()
        #Pre do some variables, that other variables rely on, because dictionaries don't maintain order
        else:
            ret = {\
                   "%relativeLocation%": self.currentPath, \
                   "%fileUUID%": self.UUID, \
                   "%fileGrpUse%": self.fileGrpUse
            }
            return ret
    
    def reload(self):
        return 
    
    def reloadFileList(self):
        return
