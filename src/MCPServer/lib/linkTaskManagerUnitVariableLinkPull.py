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

import databaseInterface
import threading
import uuid
import sys
import time
#select * from MicroServiceChainChoice JOIN MicroServiceChains on chainAvailable = MicroServiceChains.pk;
#| pk | choiceAvailableAtLink | chainAvailable | pk | startingLink | description

from linkTaskManager import linkTaskManager
from taskStandard import taskStandard
import jobChain
import databaseInterface
import os
import archivematicaMCP
global choicesAvailableForUnits
choicesAvailableForUnits = {}
choicesAvailableForUnitsLock = threading.Lock()

class linkTaskManagerUnitVariableLinkPull:
    def __init__(self, jobChainLink, pk, unit):
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.UUID = uuid.uuid4().__str__()
        self.unit = unit
        
        sql = """SELECT variable, variableValue, defaultMicroServiceChainLink FROM TasksConfigsUnitVariableLinkPull where pk = '%s'""" % (pk)
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            print row
            variable, variableValue, defaultMicroServiceChainLink = row
            row = c.fetchone()
        sqlLock.release()
        link = self.unit.getmicroServiceChainLink(variable, variableValue, defaultMicroServiceChainLink)
        
        ###Update the unit
        if link != None:
            self.jobChainLink.setExitMessage("Completed successfully")
            self.jobChainLink.jobChain.nextChainLink(link)
