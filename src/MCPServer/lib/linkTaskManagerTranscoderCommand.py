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


import math
import MySQLdb
import sys
import threading

from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard
from passClasses import ReplacementDict
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseFunctions


global outputLock
outputLock = threading.Lock()


class linkTaskManagerTranscoderCommand(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerTranscoderCommand, self).__init__(jobChainLink, pk, unit)
        global outputLock
        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.exitCode = 0
        self.clearToNextLink = False

        opts = {
            "inputFile": "%relativeLocation%",
            "fileUUID": "%fileUUID%",
            'commandClassifications': '%commandClassifications%',
            "taskUUID": "%taskUUID%",
            "objectsDirectory": "%SIPObjectsDirectory%",
            "logsDirectory": "%SIPLogsDirectory%",
            "sipUUID": "%SIPUUID%",
            "sipPath": "%SIPDirectory%",
            "fileGrpUse": "%fileGrpUse%",
            "normalizeFileGrpUse": "%normalizeFileGrpUse%",
            "excludeDirectory": "%excludeDirectory%",
            "standardErrorFile": "%standardErrorFile%",
            "standardOutputFile": "%standardOutputFile%",
        }

        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)
        for optsKey, optsValue in opts.iteritems():
            if self.jobChainLink.passVar is not None:
                if isinstance(self.jobChainLink.passVar, ReplacementDict):
                    opts[optsKey] = self.jobChainLink.passVar.replace(opts[optsKey])[0]

            commandReplacementDic = unit.getReplacementDic()
            for key, value in commandReplacementDic.iteritems():
                opts[optsKey] = opts[optsKey].replace(key, value)
            
            for key, value in SIPReplacementDic.iteritems():
                opts[optsKey] = opts[optsKey].replace(key, value)

        commandReplacementDic = unit.getReplacementDic()

        self.tasksLock.acquire()
        opts["taskUUID"] = self.UUID
        opts["FPRule"] = str(pk)
        execute = "transcoder_fprule_{0}".format(pk)
        execute = databaseFunctions.deUnicode(execute)
        self.standardOutputFile = opts["standardOutputFile"]
        self.standardErrorFile = opts["standardErrorFile"]
        self.execute = execute
        self.arguments = str(pk)
        task = taskStandard(self, execute, opts, opts["standardOutputFile"], opts["standardErrorFile"], outputLock=outputLock, UUID=self.UUID)
        self.tasks[self.UUID] = task
        databaseFunctions.logTaskCreatedSQL(self, commandReplacementDic, self.UUID, self.arguments)
        self.tasksLock.release()

        task.performTask()

    def taskCompletedCallBackFunction(self, task):
        #logTaskCompleted()
        self.exitCode += math.fabs(task.results["exitCode"])
        try:
            databaseFunctions.logTaskCompletedSQL(task)
        except MySQLdb.Warning, e:
            print >>sys.stderr, "linkTaskManagerTranscoderCommand.py task %s Suppressing mysqldb.warning: " % (task.UUID), e
        self.tasksLock.acquire()
        
        if task.UUID in self.tasks:
            del self.tasks[task.UUID]
        else:
            print >>sys.stderr, "Key Value Error:", task.UUID
            print >>sys.stderr, "Key Value Error:", self.tasks
            exit(1)

        if self.tasks == {} :
            print "DEBUG proceeding to next link", self.jobChainLink.UUID
            self.jobChainLink.linkProcessingComplete(self.exitCode, self.jobChainLink.passVar)
        self.tasksLock.release()
