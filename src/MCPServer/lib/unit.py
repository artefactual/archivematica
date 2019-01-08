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

import logging
import os

import archivematicaFunctions

from unitFile import unitFile

from main.models import File, UnitVariable

from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class unit:
    """A class to inherit from, to over-ride methods, defininging a processing object at the Job level"""

    def __init__(self, currentPath, UUID):
        self.currentPath = currentPath.__str__()
        self.UUID = UUID

    def reloadFileList(self):
        """Match files to their UUID's via their location and the File table's currentLocation"""
        self.fileList = {}
        # currentPath must be a string to return all filenames as bytestrings,
        # and to safely concatenate with other bytestrings
        currentPath = os.path.join(self.currentPath.replace("%sharedPath%", django_settings.SHARED_DIRECTORY, 1), "").encode('utf-8')
        try:
            for directory, subDirectories, files in os.walk(currentPath):
                directory = directory.replace(currentPath, self.pathString, 1)
                for file_ in files:
                    if self.pathString != directory:
                        filePath = os.path.join(directory, file_)
                    else:
                        filePath = directory + file_
                    self.fileList[filePath] = unitFile(filePath, owningUnit=self)

            if self.unitType == "Transfer":
                files = File.objects.filter(transfer_id=self.UUID)
            else:
                files = File.objects.filter(sip_id=self.UUID)
            for f in files:
                currentlocation = archivematicaFunctions.unicodeToStr(f.currentlocation)
                if currentlocation in self.fileList:
                    self.fileList[currentlocation].UUID = f.uuid
                    self.fileList[currentlocation].fileGrpUse = f.filegrpuse
                else:
                    LOGGER.warning('%s %s has file (%s) %s in the database, but file does not exist in the file system',
                                   self.unitType, self.UUID, f.uuid, f.currentlocation)
        except Exception:
            LOGGER.exception('Error reloading file list for %s', currentPath)
            exit(1)

    def setVariable(self, variable, variableValue, microServiceChainLink):
        """This gets called by linkTaskManagerSetUnitVariable.py in order to
        upsert `UnitVariable` rows for this unit. This is triggered by
        execution of a workflow chain link of type
        'linkTaskManagerSetUnitVariable'.
        """
        if not variableValue:
            variableValue = ""
        variables = UnitVariable.objects.filter(unittype=self.unitType,
                                                unituuid=self.UUID,
                                                variable=variable)
        if variables:
            LOGGER.info('Existing UnitVariables %s for %s updated to %s (MSCL'
                        ' %s)', variable, self.UUID, variableValue,
                        microServiceChainLink)
            for var in variables:
                var.variablevalue = variableValue
                var.microservicechainlink = microServiceChainLink
                var.save()
        else:
            LOGGER.info('New UnitVariable %s created for %s: %s (MSCL: %s)',
                        variable, self.UUID, variableValue,
                        microServiceChainLink)
            var = UnitVariable(
                unittype=self.unitType, unituuid=self.UUID,
                variable=variable, variablevalue=variableValue,
                microservicechainlink=microServiceChainLink
            )
            var.save()
