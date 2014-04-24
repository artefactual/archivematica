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
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict


class LinkTaskManager(object):
    """ Common manager for MicroServiceChainLinks of different task types. """
    def __init__(self, jobChainLink, pk, unit):
        """ Initalize common variables. """
        self.jobChainLink = jobChainLink
        self.pk = pk
        self.unit = unit
        self.UUID = str(uuid.uuid4())

    def update_passvar_replacement_dict(self, replace_dict):
        """ Update the ReplacementDict in the passVar, creating one if needed. """
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                # Search the list for a ReplacementDict, and update it if it
                # exists, otherwise append to list
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        passVar.update(replace_dict)
                        break
                else:
                    self.jobChainLink.passVar.append(replace_dict)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                # passVar is a ReplacementDict that needs to be updated
                self.jobChainLink.passVar.update(replace_dict)
            else:
                # Create list with existing passVar and replace_dict
                self.jobChainLink.passVar = [replace_dict, self.jobChainLink.passVar]
        else:
            # PassVar is empty, create new list
            self.jobChainLink.passVar = [replace_dict]
