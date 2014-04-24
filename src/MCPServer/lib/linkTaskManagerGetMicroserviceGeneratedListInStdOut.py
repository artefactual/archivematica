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

# Stdlib, alphabetical by import source
import os
import sys
import threading

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import databaseFunctions
from dicts import ChoicesDict, ReplacementDict


class linkTaskManagerGetMicroserviceGeneratedListInStdOut(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerGetMicroserviceGeneratedListInStdOut, self).__init__(jobChainLink, pk, unit)
        self.tasks = []
        sql = """SELECT * FROM StandardTasksConfigs where pk = '%s'""" % (pk.__str__())
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            print row
            #pk = row[0]
            filterFileEnd = row[1]
            filterFileStart = row[2]
            filterSubDir = row[3]
            self.requiresOutputLock = row[4]
            standardOutputFile = row[5]
            standardErrorFile = row[6]
            execute = row[7]
            self.execute = execute
            arguments = row[8]
            row = c.fetchone()
        sqlLock.release()

        #if reloadFileList:
        #    unit.reloadFileList()

        #        "%taskUUID%": task.UUID.__str__(), \

        if filterSubDir:
            directory = os.path.join(unit.currentPath, filterSubDir)
        else:
            directory = unit.currentPath
        
        if self.jobChainLink.passVar != None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        execute, arguments, standardOutputFile, standardErrorFile = passVar.replace(execute, arguments, standardOutputFile, standardErrorFile)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                execute, arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(execute, arguments, standardOutputFile, standardErrorFile)
                    
        commandReplacementDic = unit.getReplacementDic(directory)
                #for each key replace all instances of the key in the command string
        for key in commandReplacementDic.iterkeys():
            value = commandReplacementDic[key].replace("\"", ("\\\""))
            if execute:
                execute = execute.replace(key, value)
            if arguments:
                arguments = arguments.replace(key, value)
            if standardOutputFile:
                standardOutputFile = standardOutputFile.replace(key, value)
            if standardErrorFile:
                standardErrorFile = standardErrorFile.replace(key, value)

        self.task = taskStandard(self, execute, arguments, standardOutputFile, standardErrorFile, UUID=self.UUID)
        databaseFunctions.logTaskCreatedSQL(self, commandReplacementDic, self.UUID, arguments)
        t = threading.Thread(target=self.task.performTask)
        t.daemon = True
        t.start()

    def taskCompletedCallBackFunction(self, task):
        databaseFunctions.logTaskCompletedSQL(task)
        try:
            choices = ChoicesDict.fromstring(task.results["stdOut"])
        except Exception:
            print >>sys.stderr, "ERROR: Unable to create dic from output", \
                task.results["stdOut"], 'taskCompletedCallBackFunction'
            choices = ChoicesDict({})
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for index, value in enumerate(self.jobChainLink.passVar):
                    if isinstance(value, ChoicesDict):
                        self.jobChainLink.passVar[index] = choices
                        break
                else:
                   self.jobChainLink.passVar.append(choices)
            else:
                self.jobChainLink.passVar = [choices, self.jobChainLink.passVar] 
        else:
            self.jobChainLink.passVar = [choices]

        self.jobChainLink.linkProcessingComplete(task.results["exitCode"], self.jobChainLink.passVar)
