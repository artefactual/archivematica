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
import time
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from databaseFunctions import deUnicode
import databaseInterface

from linkTaskManager import linkTaskManager
import jobChain
import passClasses
import archivematicaMCP


class linkTaskManagerSplit:
    def __init__(self, jobChainLink, pk, unit):
        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.exitCode = 0
        self.clearToNextLink = False
        sql = """SELECT filterSubDir, execute FROM TasksConfigsStartLinkForEachFile where pk = '%s'""" % (pk.__str__())
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        
        while row != None:
            filterSubDir = deUnicode(row[0])
            self.execute = deUnicode(row[1])
            row = c.fetchone()
        sqlLock.release()
        # Check for a unit variable that specifies a normalization path
        # that overrides this
        sql = """ SELECT variableValue FROM UnitVariables WHERE unitUUID ='{unit_uuid}' AND unitType ='{unit}' AND variable='normalizationDirectory'; """.format(
            unit_uuid=unit.UUID,
            unit='SIP')
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        if row != None:
            variableValue = deUnicode(row[0])
            row = c.fetchone()
        else:
            variableValue = None
        sqlLock.release()
        if variableValue:
            filterSubDir = variableValue
        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)

        self.tasksLock.acquire()
        for file, fileUnit in unit.fileList.items():
            if filterSubDir:
                if not file.startswith(unit.pathString + filterSubDir):
                    print "skipping file", file, filterSubDir, " :   \t Doesn't start with: ", unit.pathString + filterSubDir 
                    continue

            execute = self.execute
            
            if self.jobChainLink.passVar != None:
                if isinstance(self.jobChainLink.passVar, passClasses.replacementDic):
                    execute = self.jobChainLink.passVar.replace(execute)

            commandReplacementDic = fileUnit.getReplacementDic()
            for key in commandReplacementDic:
                value = commandReplacementDic[key].replace("\"", ("\\\""))
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                if execute:
                    execute = execute.replace(key, value)
            for key in SIPReplacementDic:
                value = SIPReplacementDic[key].replace("\"", ("\\\""))
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                if execute:
                    execute = execute.replace(key, value)
            UUID = str(uuid.uuid4())
            self.tasks[UUID] = None

            t = threading.Thread(
                target=jobChain.jobChain, 
                args=(fileUnit, execute, self.taskCompletedCallBackFunction,), 
                kwargs={"passVar": self.jobChainLink.passVar, "UUID": UUID, "subJobOf": str(self.jobChainLink.UUID)} 
                )
            t.daemon = True
            while(archivematicaMCP.limitTaskThreads/2 <= threading.activeCount()):
                #print "Waiting for active threads", threading.activeCount()
                self.tasksLock.release()
                time.sleep(archivematicaMCP.limitTaskThreadsSleep)
                self.tasksLock.acquire()
            print "Active threads:", threading.activeCount()
            t.start()
        self.clearToNextLink = True
        self.tasksLock.release()
        if self.tasks == {} :
            self.jobChainLink.linkProcessingComplete(self.exitCode)


    def taskCompletedCallBackFunction(self, jobChain):
        self.tasksLock.acquire()
        if jobChain.UUID in self.tasks:
            del self.tasks[jobChain.UUID]
        else:
            print >>sys.stderr, "Key Value Error:", jobChain.UUID
            print >>sys.stderr, "Key Value Error:", self.tasks
            exit(1)

        
        if self.clearToNextLink == True and self.tasks == {} :
            print "DEBUG proceeding to next link", self.jobChainLink.UUID
            self.jobChainLink.linkProcessingComplete(self.exitCode, self.jobChainLink.passVar)
        self.tasksLock.release()
