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

from linkTaskManager import linkTaskManager
from taskStandard import taskStandard
from unitFile import unitFile
from passClasses import *
import databaseInterface
import threading
import math
import uuid
import time
import sys
import archivematicaMCP
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseFunctions
from databaseFunctions import deUnicode

import os

global outputLock
outputLock = threading.Lock()


class linkTaskManagerTranscoderCommand:
    def __init__(self, jobChainLink, pk, unit):
        global outputLock
        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.exitCode = 0
        self.clearToNextLink = False

        opts = {"inputFile":"%relativeLocation%", "fileUUID":"%fileUUID%", 'commandClassifications':'%commandClassifications%', "taskUUID":"%taskUUID%", "objectsDirectory":"%SIPObjectsDirectory%", "logsDirectory":"%SIPLogsDirectory%", "sipUUID":"%SIPUUID%", "sipPath":"%SIPDirectory%", "fileGrpUse":"%fileGrpUse%", "normalizeFileGrpUse":"%normalizeFileGrpUse%", "excludeDirectory":"%excludeDirectory%", "standardErrorFile":"%standardErrorFile%", "standardOutputFile":"%standardOutputFile%"}
        
        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)
        for optsKey, optsValue in opts.iteritems():
            if self.jobChainLink.passVar != None:
                if isinstance(self.jobChainLink.passVar, replacementDic):
                    opts[optsKey] = self.jobChainLink.passVar.replace(opts[optsKey])[0]

            commandReplacementDic = unit.getReplacementDic()
            for key, value in commandReplacementDic.iteritems():
                opts[optsKey] = opts[optsKey].replace(key, value)
            
            for key, value in SIPReplacementDic.iteritems():
                opts[optsKey] = opts[optsKey].replace(key, value)

        self.tasksLock.acquire()
        commandReplacementDic = unit.getReplacementDic()
        sql = """SELECT CommandRelationships.pk FROM CommandRelationships JOIN Commands ON CommandRelationships.command = Commands.pk WHERE CommandRelationships.pk = '%s';""" % (pk.__str__())
        rows = databaseInterface.queryAllSQL(sql)
        taskCount = 0
        if rows:
            for row in rows:
                UUID = uuid.uuid4().__str__()
                opts["taskUUID"] = UUID
                opts["CommandRelationship"] = pk.__str__()
                execute = "transcoder_cr%s" % (pk)
                deUnicode(execute)
                arguments = row.__str__()
                standardOutputFile = opts["standardOutputFile"] 
                standardErrorFile = opts["standardErrorFile"] 
                self.standardOutputFile = standardOutputFile 
                self.standardErrorFile = standardErrorFile
                self.execute = execute
                self.arguments = arguments
                task = taskStandard(self, execute, opts, standardOutputFile, standardErrorFile, outputLock=outputLock, UUID=UUID)
                self.tasks[UUID] = task
                databaseFunctions.logTaskCreatedSQL(self, commandReplacementDic, UUID, arguments)
                t = threading.Thread(target=task.performTask)
                t.daemon = True
                while(archivematicaMCP.limitTaskThreads <= threading.activeCount()):
                    #print "Waiting for active threads", threading.activeCount()
                    self.tasksLock.release()
                    time.sleep(archivematicaMCP.limitTaskThreadsSleep)
                    self.tasksLock.acquire()
                print "Active threads:", threading.activeCount()
                taskCount += 1
                t.start()


        self.clearToNextLink = True
        self.tasksLock.release()
        if taskCount == 0:
            self.jobChainLink.linkProcessingComplete(self.exitCode)


    def taskCompletedCallBackFunction(self, task):
        #logTaskCompleted()
        self.exitCode += math.fabs(task.results["exitCode"])
        databaseFunctions.logTaskCompletedSQL(task)
        self.tasksLock.acquire()
        
        if task.UUID in self.tasks:
            del self.tasks[task.UUID]
        else:
            print >>sys.stderr, "Key Value Error:", task.UUID
            print >>sys.stderr, "Key Value Error:", self.tasks
            exit(1)

        
        if self.clearToNextLink == True and self.tasks == {} :
            print "DEBUG proceeding to next link", self.jobChainLink.UUID
            self.jobChainLink.linkProcessingComplete(self.exitCode, self.jobChainLink.passVar)
        self.tasksLock.release()
