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
import uuid

import archivematicaMCP
from unit import unit
from utils import get_uuid_from_path

from main.models import Transfer

from dicts import ReplacementDict

LOGGER = logging.getLogger('archivematica.mcp.server')


class unitTransfer(unit):
    def __init__(self, path):
        self.owningUnit = None
        self.unitType = "Transfer"
        self.fileList = {}
        # Just use the end of the directory name
        self.pathString = "%transferDirectory%"
        self.currentPath = path.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

        self.init_transfer()

    def __str__(self):
        return 'unitTransfer: <UUID: {u.UUID}, path: {u.currentPath}>'.format(u=self)

    def init_transfer(self):
        """
        Populate existing transfer or create a new one.
        """
        try:
            self.transfer = Transfer.objects.get(currentlocation=self.currentPath)
            self.UUID = self.transfer.uuid
            LOGGER.info('Using existing Transfer %s at %s', self.UUID, self.currentPath)
            return
        except Transfer.DoesNotExist:
            self.UUID = get_uuid_from_path(self.currentPath)
            if self.UUID is None:
                self.UUID = str(uuid.uuid4())
            self.transfer = Transfer.objects.create(uuid=self.UUID, currentlocation=self.currentPath)
            LOGGER.info('Created new Transfer %s for %s', self.UUID, self.currentPath)

    def updateLocation(self, path):
        self.transfer.currentlocation = path
        self.transfer.save()
        self.currentPath = path

    def setMagicLink(self, link_id):
        """
        Assign a link to the unit to process when loaded.
        Deprecated! Replaced with Set/Load Unit Variable.
        """
        self.transfer.magiclink_id = link_id
        self.transfer.save()

    def getMagicLink(self):
        """
        Load a link from the unit to process.
        Deprecated! Replaced with Set/Load Unit Variable.
        """
        return (self.transfer.magiclink, self.transfer.magiclinkexitmessage)

    def reload(self):
        self.transfer = Transfer.objects.get(uuid=self.UUID)
        self.currentPath = self.transfer.currentlocation

    def getReplacementDic(self, target):
        ret = ReplacementDict.frommodel(
            type_='transfer',
            sip=self.UUID
        )
        ret["%unitType%"] = self.unitType
        return ret
