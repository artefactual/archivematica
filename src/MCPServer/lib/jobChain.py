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
import databaseInterface
from dicts import ReplacementDict
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
    sql = "SELECT variableValue FROM UnitVariables WHERE unitUUID = \"{}\" AND variable = 'replacementDict'".format(unit_uuid)
    rows, lock = databaseInterface.querySQL(sql)
    lock.release()
    if not rows:
        return results

    for replacement_dict, in rows:
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
        sql = """SELECT * FROM MicroServiceChains WHERE pk =  '%s'""" % (chainPK.__str__())
        print sql
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        if row == None:
            sqlLock.release()
            return None
        while row != None:
            print "jobChain", row
            #self.pk = row[0]
            self.startingChainLink = row[1]
            self.description = row[2]
            row = c.fetchone()
        sqlLock.release()

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

