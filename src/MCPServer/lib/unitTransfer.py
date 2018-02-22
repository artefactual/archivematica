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
import uuid

from unit import unit
from utils import isUUID

from main.models import Transfer
from dicts import ReplacementDict

from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class unitTransfer(unit):
    def __init__(self, currentPath, UUID=""):
        self.unitType = "Transfer"
        # Just use the end of the directory name
        self.pathString = "%transferDirectory%"
        currentPath2 = currentPath.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%", 1)

        if not UUID:
            try:
                transfer = Transfer.objects.get(currentlocation=currentPath2)
                UUID = transfer.uuid
                LOGGER.info('Using existing Transfer %s at %s', UUID, currentPath2)
            except Transfer.DoesNotExist:
                pass

        if not UUID:
            uuidLen = -36
            if isUUID(currentPath[uuidLen - 1:-1]):
                UUID = currentPath[uuidLen - 1:-1]
            else:
                UUID = str(uuid.uuid4())
                self.UUID = UUID
                Transfer.objects.create(uuid=UUID, currentlocation=currentPath2)

        self.currentPath = currentPath2
        self.UUID = UUID
        self.fileList = {}

    def __str__(self):
        return 'unitTransfer: <UUID: {u.UUID}, path: {u.currentPath}>'.format(u=self)

    def setMagicLink(self, link, exitStatus=""):
        """Assign a link to the unit to process when loaded.
        Deprecated! Replaced with Set/Load Unit Variable"""
        transfer = Transfer.objects.get(uuid=self.UUID)
        transfer.magiclink = link
        if exitStatus:
            transfer.magiclinkexitmessage = exitStatus
        transfer.save()

    def getMagicLink(self):
        """Load a link from the unit to process.
        Deprecated! Replaced with Set/Load Unit Variable"""
        try:
            transfer = Transfer.objects.get(uuid=self.UUID)
        except Transfer.DoesNotExist:
            return
        return (transfer.magiclink, transfer.magiclinkexitmessage)

    def reload(self):
        transfer = Transfer.objects.get(uuid=self.UUID)
        self.currentPath = transfer.currentlocation

    def getReplacementDic(self, target):
        ret = ReplacementDict.frommodel(
            type_='transfer',
            sip=self.UUID
        )
        ret["%unitType%"] = self.unitType
        return ret

    def xmlify(self):
        ret = etree.Element("unit")
        etree.SubElement(ret, "type").text = "Transfer"
        unitXML = etree.SubElement(ret, "unitXML")
        etree.SubElement(unitXML, "UUID").text = self.UUID
        tempPath = self.currentPath.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%")
        etree.SubElement(unitXML, "currentPath").text = tempPath

        return ret
