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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

import logging
import lxml.etree as etree
import os

from unit import unit

from dicts import ReplacementDict

from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class UnitDIPError(Exception):
    pass


class unitDIP(unit):
    def __init__(self, currentPath, UUID):
        self.currentPath = currentPath.__str__()
        self.UUID = UUID
        self.fileList = {}
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
        sip_directory = self.currentPath.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%")
        relative_directory_location = target.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%")

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
        etree.SubElement(unitXML, "currentPath").text = self.currentPath.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%")
        return ret
