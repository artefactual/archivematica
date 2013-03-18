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
import jobChain
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
            filterFileEnd = "" #deUnicode(row[1])
            filterFileStart = "" #deUnicode(row[2])
            filterSubDir = deUnicode(row[0])
            requiresOutputLock = "" #row[4]
            self.standardOutputFile = "" #deUnicode(row[5])
            self.standardErrorFile = "" #deUnicode(row[6])
            self.execute = deUnicode(row[1])
            self.arguments = "" #deUnicode(row[8])
            row = c.fetchone()
        sqlLock.release()
        if requiresOutputLock:
            outputLock = threading.Lock()
        else:
            outputLock = None

        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)

        self.tasksLock.acquire()
        for file, fileUnit in unit.fileList.items():
            #print "file:", file, fileUnit
            if filterFileEnd:
                if not file.endswith(filterFileEnd):
                    continue
            if filterFileStart:
                if not os.path.basename(file).startswith(filterFileStart):
                    continue
            if filterSubDir:
                #print "file", file, type(file)
                #print unit.pathString, type(unit.pathString)
                #filterSubDir = filterSubDir.encode('utf-8')
                #print filterSubDir, type(filterSubDir)

                if not file.startswith(unit.pathString + filterSubDir):
                    print "skipping file", file, filterSubDir, " :   \t Doesn't start with: ", unit.pathString + filterSubDir 
                    continue

            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            execute = self.execute
            arguments = self.arguments
            
            if self.jobChainLink.passVar != None:
                if isinstance(self.jobChainLink.passVar, replacementDic):
                    execute, arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(execute, arguments, standardOutputFile, standardErrorFile)

            commandReplacementDic = fileUnit.getReplacementDic()
            for key in commandReplacementDic.iterkeys():
                value = commandReplacementDic[key].replace("\"", ("\\\""))
                #print "key", type(key), key
                #print "value", type(value), value
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                #key = key.encode("utf-8")
                #value = value.encode("utf-8")
                if execute:
                    execute = execute.replace(key, value)
                if arguments:
                    arguments = arguments.replace(key, value)
                if standardOutputFile:
                    standardOutputFile = standardOutputFile.replace(key, value)
                if standardErrorFile:
                    standardErrorFile = standardErrorFile.replace(key, value)
            for key in SIPReplacementDic.iterkeys():
                value = SIPReplacementDic[key].replace("\"", ("\\\""))
                #print "key", type(key), key
                #print "value", type(value), value
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                #key = key.encode("utf-8")
                #value = value.encode("utf-8")

                if execute:
                    execute = execute.replace(key, value)
                if arguments:
                    arguments = arguments.replace(key, value)
                if standardOutputFile:
                    standardOutputFile = standardOutputFile.replace(key, value)
                if standardErrorFile:
                    standardErrorFile = standardErrorFile.replace(key, value)
            UUID = uuid.uuid4().__str__()
            self.tasks[UUID] = None
            ## passVar = [{preservationJobUUID, accessJobUUID, thumbnailsJobUUID}] #an idea not in use
            t = threading.Thread(target=jobChain.jobChain, args=(fileUnit, execute, self.taskCompletedCallBackFunction,), kwargs={"passVar":self.jobChainLink.passVar, "UUID":UUID, "subJobOf":self.jobChainLink.UUID.__str__()} )
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
