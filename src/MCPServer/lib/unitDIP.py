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
import os

import archivematicaMCP
from main.models import SIP
from unit import unit

from dicts import ReplacementDict

LOGGER = logging.getLogger('archivematica.mcp.server')


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
