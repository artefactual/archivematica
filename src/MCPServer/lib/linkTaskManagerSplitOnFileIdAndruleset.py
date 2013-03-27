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
import threading
import math
import uuid
import time
import sys
import archivematicaMCP
import traceback
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
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

        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)
        
        SIPUUID = unit.owningUnit.UUID
        sql = """SELECT variableValue FROM UnitVariables WHERE unitType = 'SIP' AND variable = 'normalizationFileIdentificationToolIdentifierTypes' AND unitUUID = '%s';""" % (SIPUUID)
        rows = databaseInterface.queryAllSQL(sql)
        if len(rows):
            fileIdentificationRestriction = rows[0][0]
        else:
            fileIdentificationRestriction = None
        
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

            fileUUID = unit.UUID
            ComandClassification = self.execute
            #passVar=self.jobChainLink.passVar
            toPassVar = eval(arguments)
            toPassVar.update({"%standardErrorFile%":standardErrorFile, "%standardOutputFile%":standardOutputFile, '%commandClassifications%':ComandClassification})
            #print "debug", toPassVar, toPassVar['%normalizeFileGrpUse%'], unit.fileGrpUse
            passVar=replacementDic(toPassVar)
            if toPassVar['%normalizeFileGrpUse%'] != unit.fileGrpUse or self.alreadyNormalizedManually(unit, ComandClassification):
                #print "debug: ", unit.currentPath, unit.fileGrpUse
                self.jobChainLink.linkProcessingComplete(self.exitCode, passVar=self.jobChainLink.passVar)
            else:
                taskType = databaseInterface.queryAllSQL("SELECT pk FROM TaskTypes WHERE description = '%s';" % ("Transcoder task type"))[0][0]
                if fileIdentificationRestriction:
                    sql = """SELECT MicroServiceChainLinks.pk FROM FilesIdentifiedIDs JOIN FileIDs ON FilesIdentifiedIDs.fileID = FileIDs.pk JOIN FileIDTypes ON FileIDs.fileIDType = FileIDTypes.pk JOIN CommandRelationships ON FilesIdentifiedIDs.fileID = CommandRelationships.fileID JOIN CommandClassifications ON CommandClassifications.pk = CommandRelationships.commandClassification JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = CommandRelationships.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE TasksConfigs.taskType = '%s' AND FilesIdentifiedIDs.fileUUID = '%s' AND CommandClassifications.classification = '%s' AND (%s) GROUP BY MicroServiceChainLinks.pk;""" % (taskType, fileUUID, ComandClassification, fileIdentificationRestriction)
                else:
                    sql = """SELECT MicroServiceChainLinks.pk FROM FilesIdentifiedIDs JOIN CommandRelationships ON FilesIdentifiedIDs.fileID = CommandRelationships.fileID JOIN CommandClassifications ON CommandClassifications.pk = CommandRelationships.commandClassification JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = CommandRelationships.pk JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE TasksConfigs.taskType = '%s' AND FilesIdentifiedIDs.fileUUID = '%s' AND CommandClassifications.classification = '%s' GROUP BY MicroServiceChainLinks.pk;""" % (taskType, fileUUID, ComandClassification)
                rows = databaseInterface.queryAllSQL(sql)
                if rows and len(rows):
                    for row in rows:
                         jobChainLink.jobChain.nextChainLink(row[0], passVar=passVar, incrementLinkSplit=True, subJobOf=self.jobChainLink.UUID)
                else:
                    sql = """SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications JOIN CommandClassifications ON CommandClassifications.pk = DefaultCommandsForClassifications.forClassification WHERE CommandClassifications.classification = '%s'""" % (ComandClassification)
                    rows = databaseInterface.queryAllSQL(sql)
                    for row in rows:
                         jobChainLink.jobChain.nextChainLink(row[0], passVar=passVar, incrementLinkSplit=True, subJobOf=self.jobChainLink.UUID)
                    
                self.jobChainLink.linkProcessingComplete(self.exitCode, passVar=self.jobChainLink.passVar)
    
    def alreadyNormalizedManually(self, unit, ComandClassification):
        try:
            SIPUUID = unit.owningUnit.UUID
            fileUUID = unit.UUID
            SIPPath = unit.owningUnit.currentPath
            filePath = unit.currentPath
            bname = os.path.basename(filePath)
            dirName = os.path.dirname(filePath)
            i = bname.rfind(".")
            if i != -1:
                bname = bname[:i]
            path = os.path.join(dirName, bname)
            if ComandClassification == "preservation":
                path = path.replace("%SIPDirectory%objects/", "%SIPDirectory%objects/manualNormalization/preservation/")
            elif ComandClassification == "access":
                path = path.replace("%SIPDirectory%objects/", "%SIPDirectory%objects/manualNormalization/access/")
            else:
                return False
            sql = """SELECT fileUUID FROM Files WHERE sipUUID = '%s' AND currentLocation LIKE '%s%%' AND removedTime = 0;""" % (SIPUUID, path.replace("%", "\%"))
            ret = bool(databaseInterface.queryAllSQL(sql))
            return ret 
        except Exception as inst:
            print "DEBUG EXCEPTION!"
            traceback.print_exc(file=sys.stdout)
            print type(inst)     # the exception instance
            print inst.args