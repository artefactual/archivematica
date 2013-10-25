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

from linkTaskManager import LinkTaskManager
global choicesAvailableForUnits
choicesAvailableForUnits = {}

class linkTaskManagerLoadMagicLink(LinkTaskManager):
    """Load a link from the unit to process.
        Deprecated! Replaced with Set/Load Unit Variable"""
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerLoadMagicLink, self).__init__(jobChainLink, pk, unit)
        ###Update the unit
        magicLink = self.unit.getMagicLink()
        if magicLink != None:
            link, exitStatus = magicLink
            self.jobChainLink.setExitMessage("Completed successfully")
            self.jobChainLink.jobChain.nextChainLink(link, passVar=self.jobChainLink.passVar)
