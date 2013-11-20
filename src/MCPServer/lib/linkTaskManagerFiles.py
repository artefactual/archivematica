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

import ast
import os
import threading
import time
import sys
import uuid

import archivematicaMCP
from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard
from passClasses import ReplacementDict
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import databaseFunctions
from databaseFunctions import deUnicode


class linkTaskManagerFiles(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerFiles, self).__init__(jobChainLink, pk, unit)
        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.exitCode = 0
        self.clearToNextLink = False
        sql = """SELECT * FROM StandardTasksConfigs where pk = '%s'""" % (pk.__str__())
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            filterFileEnd = deUnicode(row[1])
            filterFileStart = deUnicode(row[2])
            filterSubDir = deUnicode(row[3])
            requiresOutputLock = row[4]
            self.standardOutputFile = deUnicode(row[5])
            self.standardErrorFile = deUnicode(row[6])
            self.execute = deUnicode(row[7])
            self.arguments = deUnicode(row[8])
            row = c.fetchone()
        sqlLock.release()
        if requiresOutputLock:
            outputLock = threading.Lock()
        else:
            outputLock = None

        # Check if filterSubDir has been overridden for this Transfer/SIP
        sql = """SELECT variableValue
            FROM UnitVariables
            WHERE unitType='%s'
            AND unitUUID='%s'
            AND variable='%s';""" % (self.unit.unitType, self.unit.UUID, self.execute)
        rows = databaseInterface.queryAllSQL(sql)
        try:
            variableValue = ast.literal_eval(rows[0][0])
        except (SyntaxError, IndexError):
            # IndexError = rows was empty
            # SyntaxError = contents of variableValue weren't the expected dict
            pass
        else:
            filterSubDir = variableValue['filterSubDir']

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
                    continue

            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            execute = self.execute
            arguments = self.arguments
            
            if self.jobChainLink.passVar != None:
                if isinstance(self.jobChainLink.passVar, list):
                    for passVar in self.jobChainLink.passVar:
                        if isinstance(passVar, ReplacementDict):
                            execute, arguments, standardOutputFile, standardErrorFile = passVar.replace(execute, arguments, standardOutputFile, standardErrorFile)
                elif isinstance(self.jobChainLink.passVar, ReplacementDict):
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

            UUID = str(uuid.uuid4())
            task = taskStandard(self, execute, arguments, standardOutputFile, standardErrorFile, outputLock=outputLock, UUID=UUID)
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
            t.start()


        self.clearToNextLink = True
        self.tasksLock.release()
        if self.tasks == {} :
            self.jobChainLink.linkProcessingComplete(self.exitCode)


    def taskCompletedCallBackFunction(self, task):
        #logTaskCompleted()
        self.exitCode = max(self.exitCode, task.results["exitCode"])
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
