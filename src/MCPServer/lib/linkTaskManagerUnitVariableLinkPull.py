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

from linkTaskManager import LinkTaskManager

from main.models import Job


class linkTaskManagerUnitVariableLinkPull(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerUnitVariableLinkPull, self).__init__(jobChainLink)

        config = self.get_config()
        link_id = self.unit.getmicroServiceChainLink(config.variable)
        if not link_id:
            link_id = config.chainId  # This is really a linkId, just a naming bug

        self.jobChainLink.setExitMessage(Job.STATUS_COMPLETED_SUCCESSFULLY)
        self.jobChainLink.jobChain.next_link(link_id, passVar=self.jobChainLink.passVar)

    def get_config(self):
        return self.link.config.getUnitVar
