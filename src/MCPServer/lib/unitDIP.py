#!/usr/bin/env python2

import logging
import lxml.etree as etree
import os
import sys

import archivematicaMCP
from unit import unit

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict

LOGGER = logging.getLogger('archivematica.mcp.server')

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

    def __str__(self):
        return 'unitDIP: <UUID: {u.UUID}, path: {u.currentPath}>'.format(u=self)

    def reload(self):
        pass

    def getReplacementDic(self, target):
        ret = ReplacementDict.frommodel(
            type_='sip',
            sip=self.UUID
        )

        # augment the dict here, because DIP is a special case whose paths are
        # not entirely based on data from the database - the locations need to
        # be overridden.
        sip_directory = self.currentPath.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")
        relative_directory_location = target.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")

        ret["%SIPLogsDirectory%"] = os.path.join(sip_directory, "logs", "")
        ret["%SIPObjectsDirectory%"] = os.path.join(sip_directory, "objects", "")
        ret["%SIPDirectory%"] = sip_directory
        ret["%SIPDirectoryBasename"] = os.path.basename(os.path.abspath(sip_directory))
        ret["%relativeLocation%"] = target.replace(self.currentPath, relative_directory_location, 1)
        ret["%unitType%"] = "DIP"
        return ret

    def xmlify(self):
        ret = etree.Element("unit")
        etree.SubElement(ret, "type").text = "DIP"
        unitXML = etree.SubElement(ret, "unitXML")
        etree.SubElement(unitXML, "UUID").text = self.UUID
        etree.SubElement(unitXML, "currentPath").text = self.currentPath.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%")
        return ret
