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
import uuid
import MySQLdb
from linkTaskManagerDirectories import linkTaskManagerDirectories
from linkTaskManagerFiles import linkTaskManagerFiles
from linkTaskManagerChoice import linkTaskManagerChoice
from linkTaskManagerAssignMagicLink import linkTaskManagerAssignMagicLink
from linkTaskManagerLoadMagicLink import linkTaskManagerLoadMagicLink
from linkTaskManagerReplacementDicFromChoice import linkTaskManagerReplacementDicFromChoice
from linkTaskManagerSplit import linkTaskManagerSplit
from linkTaskManagerSplitOnFileIdAndruleset import linkTaskManagerSplitOnFileIdAndruleset
from linkTaskManagerTranscoderCommand import linkTaskManagerTranscoderCommand
from linkTaskManagerGetMicroserviceGeneratedListInStdOut import linkTaskManagerGetMicroserviceGeneratedListInStdOut
from linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList import linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from databaseFunctions import logJobCreatedSQL
from playAudioFileInCVLC import playAudioFileInThread

#Constants
# SELECT * FROM TaskTypes;
constOneTask = 0
constTaskForEachFile = 1
constSelectPathTask = 2
constSetMagicLink = 3
constLoadMagicLink = 4
constGetReplacementDic = 5
constSplitByFile = 6
constlinkTaskManagerSplitOnFileIdAndruleset = 7
constTranscoderTaskLink = 8
constlinkTaskManagerGetMicroserviceGeneratedListInStdOut = 9
constlinkTaskManagerGetUserChoiceFromMicroserviceGeneratedList = 10

class jobChainLink:
    def __init__(self, jobChain, jobChainLinkPK, unit, passVar=None, subJobOf=""):
        if jobChainLinkPK == None:
            return None
        self.UUID = uuid.uuid4().__str__()
        self.jobChain = jobChain
        self.pk = jobChainLinkPK
        self.unit = unit
        self.passVar=passVar
        self.createdDate = databaseInterface.getUTCDate()
        self.subJobOf = subJobOf
        sql = """SELECT MicroServiceChainLinks.currentTask, MicroServiceChainLinks.defaultNextChainLink, TasksConfigs.taskType, TasksConfigs.taskTypePKReference, TasksConfigs.description, MicroServiceChainLinks.reloadFileList, Sounds.fileLocation, MicroServiceChainLinks.defaultExitMessage, MicroServiceChainLinks.microserviceGroup FROM MicroServiceChainLinks LEFT OUTER JOIN Sounds ON MicroServiceChainLinks.defaultPlaySound = Sounds.pk JOIN TasksConfigs on MicroServiceChainLinks.currentTask = TasksConfigs.pk WHERE MicroServiceChainLinks.pk = """ + jobChainLinkPK.__str__()
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        if row == None:
            sqlLock.release()
            return None
        while row != None:
            print row
            self.currentTask = row[0]
            self.defaultNextChainLink = row[1]
            taskType = row[2]
            taskTypePKReference = row[3]
            self.description = row[4]
            self.reloadFileList = row[5]
            self.defaultSoundFile = row[6]
            self.defaultExitMessage = row[7]
            self.microserviceGroup = row[8]
            row = c.fetchone()
        sqlLock.release()



        print "<<<<<<<<< ", self.description, " >>>>>>>>>"
        self.unit.reload()

        logJobCreatedSQL(self)

        if self.createTasks(taskType, taskTypePKReference) == None:
            self.getNextChainLinkPK(None)
            #can't have none represent end of chain, and no tasks to process.
            #could return negative?

    def createTasks(self, taskType, taskTypePKReference):
        if taskType == constOneTask:
            linkTaskManagerDirectories(self, taskTypePKReference, self.unit)
        elif taskType == constTaskForEachFile:
            if self.reloadFileList:
                self.unit.reloadFileList();
            linkTaskManagerFiles(self, taskTypePKReference, self.unit)
        elif taskType == constSelectPathTask:
            linkTaskManagerChoice(self, taskTypePKReference, self.unit)
        elif taskType == constSetMagicLink:
            linkTaskManagerAssignMagicLink(self, taskTypePKReference, self.unit)
        elif taskType == constLoadMagicLink:
            linkTaskManagerLoadMagicLink(self, taskTypePKReference, self.unit)
        elif taskType == constGetReplacementDic:
            linkTaskManagerReplacementDicFromChoice(self, taskTypePKReference, self.unit)
        elif taskType == constSplitByFile:
            if self.reloadFileList:
                self.unit.reloadFileList();
            linkTaskManagerSplit(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerSplitOnFileIdAndruleset:
            if self.reloadFileList:
                self.unit.reloadFileList();
            linkTaskManagerSplitOnFileIdAndruleset(self, taskTypePKReference, self.unit)
        elif taskType == constTranscoderTaskLink:
            if self.reloadFileList:
                self.unit.reloadFileList();
            linkTaskManagerTranscoderCommand(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerGetMicroserviceGeneratedListInStdOut:
            linkTaskManagerGetMicroserviceGeneratedListInStdOut(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerGetUserChoiceFromMicroserviceGeneratedList:
            linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList(self, taskTypePKReference, self.unit)
        else:
            print sys.stderr, "unsupported task type: ", taskType

    def getSoundFileToPlay(self, exitCode):
        if exitCode != None:
            ret = self.defaultSoundFile
            sql = "SELECT Sounds.fileLocation FROM MicroServiceChainLinksExitCodes LEFT OUTER JOIN Sounds ON MicroServiceChainLinksExitCodes.playSound = Sounds.pk WHERE microServiceChainLink = %s AND exitCode = %s" % (self.pk.__str__(), exitCode.__str__())
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            if row != None:
                ret = row[0]
            sqlLock.release()
            return ret

    def getNextChainLinkPK(self, exitCode):
        if exitCode != None:
            ret = self.defaultNextChainLink
            sql = "SELECT nextMicroServiceChainLink FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink = %s AND exitCode = %s" % (self.pk.__str__(), exitCode.__str__())
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            if row != None:
                ret = row[0]
            sqlLock.release()
            return ret

    def setExitMessage(self, message):
        databaseInterface.runSQL("UPDATE Jobs " + \
                "SET currentStep='" + MySQLdb.escape_string(message.__str__()) +  "' " + \
                "WHERE jobUUID='" + self.UUID + "'" )

    def updateExitMessage(self, exitCode):
        ret = self.defaultExitMessage
        if exitCode != None:
            sql = "SELECT exitMessage FROM MicroServiceChainLinksExitCodes WHERE microServiceChainLink = %s AND exitCode = %s" % (self.pk.__str__(), exitCode.__str__())
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            if row != None:
                ret = row[0]
            sqlLock.release()
        if ret != None:
            self.setExitMessage(ret)
        else:
            print "No exit message"

    def linkProcessingComplete(self, exitCode, passVar=None):
        playSounds = True
        if playSounds:
            filePath = self.getSoundFileToPlay(exitCode)
            if filePath:
                print "playing: ", filePath
                playAudioFileInThread(filePath)
        self.updateExitMessage(exitCode)
        self.jobChain.nextChainLink(self.getNextChainLinkPK(exitCode), passVar=passVar)
