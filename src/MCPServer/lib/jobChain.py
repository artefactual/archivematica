#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @version svn: $Id$

import sys
import threading
from jobChainLink import jobChainLink
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
#Holds:
#-UNIT
#-Job chain link
#-Job chain description
#
#potentialToHold/getFromDB
#-previous chain links
class jobChain:
    def __init__(self, unit, chainPK, notifyComplete=None, passVar=None, UUID=None, subJobOf=""):
        print "jobChain",  unit, chainPK
        if chainPK == None:
            return None
        self.unit = unit
        self.pk = chainPK
        self.notifyComplete = notifyComplete
        self.UUID = UUID
        self.linkSplitCount = 1
        self.subJobOf = subJobOf
        sql = """SELECT * FROM MicroServiceChains WHERE pk =  """ + chainPK.__str__()
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
        self.currentLink = jobChainLink(self, self.startingChainLink, unit, passVar=passVar, subJobOf=subJobOf)
        if self.currentLink == None:
            return None

    def nextChainLink(self, pk, passVar=None, incrementLinkSplit=False, subJobOf=""):
        if self.subJobOf and not subJobOf:
            subJobOf = self.subJobOf
        if incrementLinkSplit:
            self.linkSplitCount += 1
        if pk != None:
            # may 2012 - can't think why I'm threading this - TODO 
            # I think it was threaded to avoid nasty stack trace problems
            #t = threading.Thread(target=self.nextChainLinkThreaded, args=(pk,), kwargs={"passVar":passVar} )
            #t.daemon = True
            #t.start()
            jobChainLink(self, pk, self.unit, passVar=passVar, subJobOf=subJobOf)
        else:
            self.linkSplitCount -= 1
            if self.linkSplitCount == 0:
                print "Done with UNIT:" + self.unit.UUID
                if self.notifyComplete:
                    self.notifyComplete(self)

    def nextChainLinkThreaded(self, pk, passVar=None):
        self.currentLink = jobChainLink(self, pk, self.unit, passVar)
