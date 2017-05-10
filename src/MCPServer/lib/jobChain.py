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

from dicts import ReplacementDict
from jobChainLink import jobChainLink
from main.models import UnitVariable

LOGGER = logging.getLogger('archivematica.mcp.server')


def fetchUnitVariableForUnit(unit_uuid):
    """
    Returns a dict combining all of the replacementDict unit variables for the
    specified unit.
    """
    results = ReplacementDict()
    variables = UnitVariable.objects.filter(unituuid=unit_uuid, variable="replacementDict").values_list('variablevalue')

    for replacement_dict, in variables:
        rd = ReplacementDict.fromstring(replacement_dict)
        results.update(rd)

    return results


class jobChain:
    """
    Represents a workflow chain and controls its execution.
    """
    def __init__(self, unit, chain_id, workflow, unit_choices):
        self.unit = unit
        self.pk = chain_id
        self.workflow = workflow
        self.unit_choices = unit_choices

        self.chain = self.workflow.chains[self.pk]
        if self.chain is None:
            LOGGER.error('jobChain error: chain %s not found (unit=%s)', chain_id, unit)
            return
        LOGGER.debug('Creating jobChain (chain=%s, unit=%s)', chain_id, unit)

        # Migrate over unit variables containing replacement dicts from previous chains,
        # but prioritize any values contained in passVars passed in as kwargs
        rd = fetchUnitVariableForUnit(unit.UUID)

        # Start processing
        self.next_link(self.chain.linkId, passVar=rd)

    def next_link(self, link_id, passVar=None):
        """
        Proceed to next link, as passed (link_id).
        """
        if not link_id:
            return  # End of chain!
        LOGGER.debug('Moving to next link id=%s', link_id)
        jobChainLink(self, link_id, self.unit, passVar=passVar)
