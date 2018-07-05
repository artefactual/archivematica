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

choicesAvailableForUnits = {}

from main.models import TaskConfigUnitVariableLinkPull


class linkTaskManagerUnitVariableLinkPull(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerUnitVariableLinkPull, self).__init__(jobChainLink,
                                                                  pk, unit)

        # Look up the variable entry in the workflow data.
        var = TaskConfigUnitVariableLinkPull.objects.get(id=pk)

        # Determine the next link.
        link = self.unit.getmicroServiceChainLink(
            var.variable,
            var.variablevalue,
            var.defaultmicroservicechainlink)

        if link is None:
            return

        # Mark as complete and continue.
        self.jobChainLink.linkProcessingComplete(
            exitCode=0,
            passVar=self.jobChainLink.passVar,
            next_link_id=link.id)
