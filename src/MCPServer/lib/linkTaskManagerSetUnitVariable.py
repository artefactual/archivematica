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


class linkTaskManagerSetUnitVariable(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerSetUnitVariable, self).__init__(
            jobChainLink, unit)
        config = self.jobChainLink.link.config
        self.unit.setVariable(
            config["variable"], config["variable_value"], config["chain_id"])
        self.jobChainLink.linkProcessingComplete(exitCode=0)
