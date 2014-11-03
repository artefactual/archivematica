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
import uuid
import MySQLdb
from linkTaskManagerDirectories import linkTaskManagerDirectories
from linkTaskManagerFiles import linkTaskManagerFiles
from linkTaskManagerChoice import linkTaskManagerChoice
from linkTaskManagerAssignMagicLink import linkTaskManagerAssignMagicLink
from linkTaskManagerLoadMagicLink import linkTaskManagerLoadMagicLink
from linkTaskManagerReplacementDicFromChoice import linkTaskManagerReplacementDicFromChoice
from linkTaskManagerGetMicroserviceGeneratedListInStdOut import linkTaskManagerGetMicroserviceGeneratedListInStdOut
from linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList import linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList
from linkTaskManagerSetUnitVariable import linkTaskManagerSetUnitVariable
from linkTaskManagerUnitVariableLinkPull import linkTaskManagerUnitVariableLinkPull
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from databaseFunctions import logJobCreatedSQL, getUTCDate
from playAudioFileInCVLC import playAudioFileInThread
sys.path.append("/usr/share/archivematica/dashboard")
from main.models import Job, MicroServiceChainLink, MicroServiceChainLinkExitCode, TaskType

# Constants
constOneTask = TaskType.objects.get(description="one instance").pk
constTaskForEachFile = TaskType.objects.get(description="for each file").pk
constSelectPathTask = TaskType.objects.get(description="get user choice to proceed with").pk
constSetMagicLink = TaskType.objects.get(description="assign magic link").pk
constLoadMagicLink = TaskType.objects.get(description="goto magic link").pk
constGetReplacementDic = TaskType.objects.get(description="get replacement dic from user choice").pk
constlinkTaskManagerGetMicroserviceGeneratedListInStdOut = TaskType.objects.get(description="Get microservice generated list in stdOut").pk
constlinkTaskManagerGetUserChoiceFromMicroserviceGeneratedList = TaskType.objects.get(description="Get user choice from microservice generated list").pk
constlinkTaskManagerSetUnitVariable = TaskType.objects.get(description="linkTaskManagerSetUnitVariable").pk
constlinkTaskManagerUnitVariableLinkPull = TaskType.objects.get(description="linkTaskManagerUnitVariableLinkPull").pk

class jobChainLink:
    def __init__(self, jobChain, jobChainLinkPK, unit, passVar=None, subJobOf=""):
        if jobChainLinkPK == None:
            return None
        self.UUID = uuid.uuid4().__str__()
        self.jobChain = jobChain
        self.unit = unit
        self.passVar=passVar
        self.createdDate = getUTCDate()
        self.subJobOf = subJobOf

        # Depending on the path that led to this, jobChainLinkPK may
        # either be a UUID or a MicroServiceChainLink instance
        if isinstance(jobChainLinkPK, basestring):
            try:
                link = MicroServiceChainLink.objects.get(id=str(jobChainLinkPK))
            # This will sometimes return no values
            except MicroServiceChainLink.DoesNotExist:
                return
        else:
            link = jobChainLinkPK

        self.pk = link.id

        self.currentTask = link.currenttask_id
        self.defaultNextChainLink = link.defaultnextchainlink_id
        taskType = link.currenttask.tasktype_id
        taskTypePKReference = link.currenttask.tasktypepkreference
        self.description = link.currenttask.description
        self.reloadFileList = link.reloadfilelist
        self.defaultSoundFile = None
        self.defaultExitMessage = link.defaultexitmessage
        self.microserviceGroup = link.microservicegroup

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
        elif taskType == constlinkTaskManagerGetMicroserviceGeneratedListInStdOut:
            linkTaskManagerGetMicroserviceGeneratedListInStdOut(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerGetUserChoiceFromMicroserviceGeneratedList:
            linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerUnitVariableLinkPull:
            linkTaskManagerUnitVariableLinkPull(self, taskTypePKReference, self.unit)
        elif taskType == constlinkTaskManagerSetUnitVariable:
            linkTaskManagerSetUnitVariable(self, taskTypePKReference, self.unit)
        else:
            print >> sys.stderr, "unsupported task type: ", taskType

    # Deprecated, remove later
    def getSoundFileToPlay(self, exitCode):
        return self.defaultSoundFile

    def getNextChainLinkPK(self, exitCode):
        if exitCode is not None:
            try:
                return MicroServiceChainLinkExitCode.objects.get(microservicechainlink_id=str(self.pk), exitcode=str(exitCode)).nextmicroservicechainlink_id
            except (MicroServiceChainLinkExitCode.DoesNotExist, MicroServiceChainLinkExitCode.MultipleObjectsReturned):
                return self.defaultNextChainLink

    def setExitMessage(self, message):
        Job.objects.filter(jobuuid=self.UUID).update(currentstep=str(message))

    def updateExitMessage(self, exitCode):
        message = self.defaultExitMessage
        if exitCode is not None:
            try:
                message = MicroServiceChainLinkExitCode.objects.get(microservicechainlink_id=str(self.pk), exitcode=str(exitCode)).exitmessage
            except MicroServiceChainLinkExitCode.DoesNotExist:
                pass
        if message is not None:
            self.setExitMessage(message)
        else:
            print "No exit message"

    def linkProcessingComplete(self, exitCode, passVar=None):
        # Deprecated, remove later
        playSounds = True
        if playSounds:
            filePath = self.getSoundFileToPlay(exitCode)
            if filePath:
                print "playing: ", filePath
                playAudioFileInThread(filePath)
        self.updateExitMessage(exitCode)
        self.jobChain.nextChainLink(self.getNextChainLinkPK(exitCode), passVar=passVar)
