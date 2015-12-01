#!/usr/bin/env python2

import logging
import os
import sys

import archivematicaMCP
from unitFile import unitFile

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import File, UnitVariable

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
        currentPath = str(self.currentPath.replace("%sharedPath%", \
                                                       archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1) + "/")
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
                if f.currentlocation in self.fileList:
                    self.fileList[f.currentlocation].UUID = f.uuid
                    self.fileList[f.currentlocation].fileGrpUse = f.filegrpuse
                else:
                    LOGGER.warning('%s %s has file (%s) %s in the database, but file does not exist in the file system',
                        self.unitType, self.UUID, f.uuid, f.currentlocation)
        except Exception:
            LOGGER.exception('Error reloading file list for %s', currentPath)
            exit(1)

    def getMagicLink(self):
        return

    def setMagicLink(self, link, exitStatus=""):
        return

    def setVariable(self, variable, variableValue, microServiceChainLink):
        if not variableValue:
            variableValue = ""
        variables = UnitVariable.objects.filter(unittype=self.unitType,
                                           unituuid=self.UUID,
                                           variable=variable)
        if variables:
            LOGGER.info('Existing UnitVariables for %s updated to %s (MSCL %s)', variable, variableValue, microServiceChainLink)
            for var in variables:
                var.variablevalue = variableValue
                var.microservicechainlink_id = microServiceChainLink
                var.save()
        else:
            LOGGER.info('New UnitVariable created for %s: %s (MSCL: %s)', variable, variableValue, microServiceChainLink)
            var = UnitVariable(
                unittype=self.unitType, unituuid=self.UUID,
                variable=variable, variablevalue=variableValue,
                microservicechainlink_id=microServiceChainLink
            )
            var.save()

    # NOTE: variableValue argument is currently unused.
    def getmicroServiceChainLink(self, variable, variableValue, defaultMicroServiceChainLink):
        LOGGER.debug('Fetching MicroServiceChainLink for %s (default %s)', variable, defaultMicroServiceChainLink)
        try:
            var = UnitVariable.objects.get(unittype=self.unitType,
                                           unituuid=self.UUID,
                                           variable=variable)
            return var.microservicechainlink
        except UnitVariable.DoesNotExist:
            return defaultMicroServiceChainLink
