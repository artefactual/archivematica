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


class linkTaskManagerSplitOnFileIdAndruleset:
    def __init__(self, jobChainLink, pk, unit):
        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.pk = pk
        self.jobChainLink = jobChainLink
        self.exitCode = 0
        self.clearToNextLink = False
        sql = """SELECT * FROM StandardTasksConfigs where pk = """ + pk.__str__()
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
                    print "skipping file", file, filterSubDir
                    continue

            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            execute = self.execute
            arguments = self.arguments
            
            if self.jobChainLink.passVar != None:
                if isinstance(self.jobChainLink.passVar, replacementDic):
                    execute, arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(execute, arguments, standardOutputFile, standardErrorFile)

            fileUUID = unit.UUID
            ComandClassification = self.execute
            #passVar=self.jobChainLink.passVar
            toPassVar = eval(arguments)
            toPassVar.update({"%standardErrorFile%":standardErrorFile, "%standardOutputFile%":standardOutputFile, '%commandClassifications%':ComandClassification})
            print "debug", toPassVar
            passVar=replacementDic(toPassVar)
            sql = """SELECT MicroServiceChainLinks.pk FROM FilesIdentifiedIDs JOIN CommandRelationships ON FilesIdentifiedIDs.fileID = CommandRelationships.fileID JOIN CommandClassifications ON CommandClassifications.pk = CommandRelationships.commandClassification JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = CommandRelationships.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE TasksConfigs.taskType = 8 AND FilesIdentifiedIDs.fileUUID = '%s' AND CommandClassifications.classification = '%s';""" % (fileUUID, ComandClassification)
            rows = databaseInterface.queryAllSQL(sql)
            if rows and len(rows):
                print "DEBUGGING 6772: ", fileUUID, ComandClassification, rows
                for row in rows:
                     jobChainLink.jobChain.nextChainLink(row[0], passVar=passVar, incrementLinkSplit=True, subJobOf=self.jobChainLink.UUID)
            else:
                sql = """SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications JOIN CommandClassifications ON CommandClassifications.pk = DefaultCommandsForClassifications.forClassification WHERE CommandClassifications.classification = '%s'""" % (ComandClassification)
                rows = databaseInterface.queryAllSQL(sql)
                print "DEBUGGING2 6772: ", fileUUID, ComandClassification, rows
                for row in rows:
                     jobChainLink.jobChain.nextChainLink(row[0], passVar=passVar, incrementLinkSplit=True, subJobOf=self.jobChainLink.UUID)
                
            self.jobChainLink.linkProcessingComplete(self.exitCode, passVar=self.jobChainLink.passVar)