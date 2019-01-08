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

from main.models import UnitVariable

choicesAvailableForUnits = {}


class linkTaskManagerUnitVariableLinkPull(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerUnitVariableLinkPull, self).__init__(
            jobChainLink, unit)
        next_link = self._get_next_link()
        if next_link is None:
            raise Exception(
                "linkTaskManagerUnitVariableLinkPull could not find next link")
        self.jobChainLink.linkProcessingComplete(
            exitCode=0,
            passVar=self.jobChainLink.passVar,
            next_link=next_link)

    def _get_next_link(self):
        """Look up next chain link in UnitVariable."""
        link = self.jobChainLink.link
        try:
            unitvar = UnitVariable.objects.get(
                unittype=self.unit.unitType, unituuid=self.unit.UUID,
                variable=link.config["variable"])
        except UnitVariable.DoesNotExist:
            link_id = link.config["chain_id"]
        else:
            link_id = unitvar.microservicechainlink
        try:
            link = self.jobChainLink.workflow.get_link(link_id)
        except KeyError:
            return
        return link
