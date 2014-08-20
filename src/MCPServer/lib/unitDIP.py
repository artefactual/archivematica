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

from unit import unit
from unitFile import unitFile
import archivematicaMCP
import os
import sys
import lxml.etree as etree

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import File

class UnitDIPError(Exception):
    pass

class unitDIP(unit):

    def __init__(self, currentPath, UUID):
        self.currentPath = currentPath.__str__()
        self.UUID = UUID
        self.fileList = {}
        self.owningUnit = None
        self.pathString = "%SIPDirectory%"
        self.unitType = "DIP"

    def reload(self):
        #sql = """SELECT * FROM SIPs WHERE sipUUID =  '""" + self.UUID + "'"
        #c, sqlLock = databaseInterface.querySQL(sql)
        #row = c.fetchone()
        #while row != None:
        #    print row
        #    #self.UUID = row[0]
        #    self.createdTime = row[1]
        #    self.currentPath = row[2]
        #    row = c.fetchone()
        #sqlLock.release()

        #no-op for reload on DIP
        return

    def getReplacementDic(self, target):
        # self.currentPath = currentPath.__str__()
        # self.UUID = uuid.uuid4().__str__()
        #Pre do some variables, that other variables rely on, because dictionaries don't maintain order
        SIPUUID = self.UUID
        if self.currentPath.endswith("/"):
            SIPName = os.path.basename(self.currentPath[:-1]).replace("-" + SIPUUID, "")
        else:
            SIPName = os.path.basename(self.currentPath).replace("-" + SIPUUID, "")
        SIPDirectory = self.currentPath.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")
        relativeDirectoryLocation = target.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")


        ret = { \
        "%SIPLogsDirectory%": SIPDirectory + "logs/", \
        "%SIPObjectsDirectory%": SIPDirectory + "objects/", \
        "%SIPDirectory%": SIPDirectory, \
        "%SIPDirectoryBasename%": os.path.basename(os.path.abspath(SIPDirectory)), \
        "%relativeLocation%": target.replace(self.currentPath, relativeDirectoryLocation, 1), \
        "%processingDirectory%": archivematicaMCP.config.get('MCPServer', "processingDirectory"), \
        "%checksumsNoExtention%":archivematicaMCP.config.get('MCPServer', "checksumsNoExtention"), \
        "%watchDirectoryPath%":archivematicaMCP.config.get('MCPServer', "watchDirectoryPath"), \
        "%rejectedDirectory%":archivematicaMCP.config.get('MCPServer', "rejectedDirectory"), \
        "%SIPUUID%":SIPUUID, \
        "%SIPName%":SIPName, \
        "%unitType%":"DIP" \
        }
        return ret

    def xmlify(self):
        ret = etree.Element("unit")
        etree.SubElement(ret, "type").text = "DIP"
        unitXML = etree.SubElement(ret, "unitXML")
        etree.SubElement(unitXML, "UUID").text = self.UUID
        etree.SubElement(unitXML, "currentPath").text = self.currentPath.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")
        return ret
