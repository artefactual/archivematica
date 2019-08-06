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

import uuid

from dicts import ReplacementDict


class LinkTaskManager(object):
    """ Common manager for MicroServiceChainLinks of different task types. """

    def __init__(self, jobChainLink, unit):
        """ Initalize common variables. """
        self.jobChainLink = jobChainLink
        self.unit = unit
        self.UUID = str(uuid.uuid4())

    def update_passvar_replacement_dict(self, replace_dict):
        """ Update the ReplacementDict in the passVar, creating one if needed. """
        if self.jobChainLink.pass_var is not None:
            if isinstance(self.jobChainLink.pass_var, list):
                # Search the list for a ReplacementDict, and update it if it
                # exists, otherwise append to list
                for passVar in self.jobChainLink.pass_var:
                    if isinstance(passVar, ReplacementDict):
                        passVar.update(replace_dict)
                        break
                else:
                    self.jobChainLink.pass_var.append(replace_dict)
            elif isinstance(self.jobChainLink.pass_var, ReplacementDict):
                # passVar is a ReplacementDict that needs to be updated
                self.jobChainLink.pass_var.update(replace_dict)
            else:
                # Create list with existing passVar and replace_dict
                self.jobChainLink.pass_var = [replace_dict, self.jobChainLink.pass_var]
        else:
            # PassVar is empty, create new list
            self.jobChainLink.pass_var = [replace_dict]
