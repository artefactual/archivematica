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
import threading
from jobChainLink import jobChainLink
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from dicts import ReplacementDict
sys.path.append("/usr/share/archivematica/dashboard")
from main.models import MicroServiceChain, UnitVariable
#Holds:
#-UNIT
#-Job chain link
#-Job chain description
#
#potentialToHold/getFromDB
#-previous chain links


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
    def __init__(self, unit, chainPK, notifyComplete=None, passVar=None, UUID=None, subJobOf=""):
        """Create an instance of a chain from the MicroServiceChains table"""
        print "jobChain",  unit, chainPK
        if chainPK == None:
            return None
        self.unit = unit
        self.pk = chainPK
        self.notifyComplete = notifyComplete
        self.UUID = UUID
        self.linkSplitCount = 1
        self.subJobOf = subJobOf

        chain = MicroServiceChain.objects.get(id=str(chainPK))
        print "jobChain", chain
        self.startingChainLink = chain.startinglink_id
        self.description = chain.description

        # Migrate over unit variables containing replacement dicts from previous chains,
        # but prioritize any values contained in passVars passed in as kwargs
        rd = fetchUnitVariableForUnit(unit.UUID)
        if passVar:
            rd.update(passVar)

        self.currentLink = jobChainLink(self, self.startingChainLink, unit, passVar=rd, subJobOf=subJobOf)
        if self.currentLink == None:
            return None

    def nextChainLink(self, pk, passVar=None, incrementLinkSplit=False, subJobOf=""):
        """Proceed to next link, as passed(pk)"""
        if self.subJobOf and not subJobOf:
            subJobOf = self.subJobOf
        if incrementLinkSplit:
            self.linkSplitCount += 1
        if pk != None:
            jobChainLink(self, pk, self.unit, passVar=passVar, subJobOf=subJobOf)
        else:
            self.linkSplitCount -= 1
            if self.linkSplitCount == 0:
                print "Done with UNIT:" + self.unit.UUID
                if self.notifyComplete:
                    self.notifyComplete(self)

