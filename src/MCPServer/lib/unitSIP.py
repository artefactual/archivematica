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

from unit import unit

from main.models import SIP

from dicts import ReplacementDict

from django.conf import settings as django_settings

LOGGER = logging.getLogger('archivematica.mcp.server')


class unitSIP(unit):
    def __init__(self, currentPath, UUID):
        self.currentPath = currentPath.__str__()
        self.UUID = UUID
        self.fileList = {}
        self.pathString = "%SIPDirectory%"
        self.unitType = "SIP"
        self.aipFilename = ""

    def __str__(self):
        return 'unitSIP: <UUID: {u.UUID}, path: {u.currentPath}>'.format(u=self)

    def setMagicLink(self, link, exitStatus=""):
        """Assign a link to the unit to process when loaded.
        Deprecated! Replaced with Set/Load Unit Variable"""
        sip = SIP.objects.get(uuid=self.UUID)
        sip.magiclink = link
        if exitStatus:
            sip.magiclinkexitmessage = exitStatus
        sip.save()

    def getMagicLink(self):
        """Load a link from the unit to process.
        Deprecated! Replaced with Set/Load Unit Variable"""
        try:
            sip = SIP.objects.get(uuid=self.UUID)
        except SIP.DoesNotExist:
            return
        return (sip.magiclink, sip.magiclinkexitmessage)

    def reload(self):
        sip = SIP.objects.get(uuid=self.UUID)
        self.createdTime = sip.createdtime
        self.currentPath = sip.currentpath
        self.aipFilename = sip.aip_filename or ""
        self.sipType = sip.sip_type

    def getReplacementDic(self, target):
        """ Return a dict with all of the replacement strings for this unit and the value to replace with. """
        ret = ReplacementDict.frommodel(
            type_='sip',
            sip=self.UUID
        )
        ret["%AIPFilename%"] = self.aipFilename
        ret["%unitType%"] = self.unitType
        ret["%SIPType%"] = self.sipType
        return ret

    def xmlify(self):
        ret = etree.Element("unit")
        etree.SubElement(ret, "type").text = "SIP"
        unitXML = etree.SubElement(ret, "unitXML")
        etree.SubElement(unitXML, "UUID").text = self.UUID
        etree.SubElement(unitXML, "currentPath").text = self.currentPath.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%")
        return ret
