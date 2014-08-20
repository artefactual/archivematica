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

import sys

from linkTaskManager import LinkTaskManager

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import TaskConfigAssignMagicLink

global choicesAvailableForUnits
choicesAvailableForUnits = {}

class linkTaskManagerAssignMagicLink(LinkTaskManager):
    """Assign a link to the unit to process when loaded.
        Deprecated! Replaced with Set/Load Unit Variable"""
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerAssignMagicLink, self).__init__(jobChainLink, pk, unit)

        ###GET THE MAGIC NUMBER FROM THE TASK stuff
        link = 0
        try:
            link = TaskConfigAssignMagicLink.objects.get(id=pk).execute
        except TaskConfigAssignMagicLink.DoesNotExist:
            pass

        ###Update the unit
        #set the magic number
        self.unit.setMagicLink(link, exitStatus="")
        self.jobChainLink.linkProcessingComplete(0)
