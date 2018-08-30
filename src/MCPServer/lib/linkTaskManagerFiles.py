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
import logging
import os
import threading

from django.conf import settings as django_settings

from linkTaskManager import LinkTaskManager
import archivematicaFunctions
from dicts import ReplacementDict
from main.models import StandardTaskConfig, UnitVariable

from taskGroupRunner import TaskGroupRunner
from taskGroup import TaskGroup

LOGGER = logging.getLogger('archivematica.mcp.server')

# The number of files we'll pack into each MCP Client job.  Chosen somewhat
# arbitrarily, but benchmarking with larger values (like 512) didn't make much
# difference to throughput.
#
# Setting this too large will use more memory; setting it too small will hurt
# throughput.  So the trick is to set it juuuust right.
BATCH_SIZE = django_settings.BATCH_SIZE


class linkTaskManagerFiles(LinkTaskManager):
    def __init__(self, jobChainLink, pk, unit):
        super(linkTaskManagerFiles, self).__init__(jobChainLink, pk, unit)

        if jobChainLink.reloadFileList:
            unit.reloadFileList()

        # The list of task groups we'll be executing for this batch of files
        self.taskGroupsLock = threading.Lock()
        self.taskGroups = {}

        # Zero if every taskGroup executed so far has succeeded.  Otherwise,
        # something greater than zero.
        self.exitCode = 0

        self.clearToNextLink = False

        stc = StandardTaskConfig.objects.get(id=str(pk))
        # These three may be concatenated/compared with other strings,
        # so they need to be bytestrings here
        filterFileEnd = str(stc.filter_file_end) if stc.filter_file_end else ''
        filterFileStart = str(stc.filter_file_start) if stc.filter_file_start else ''
        filterSubDir = str(stc.filter_subdir) if stc.filter_subdir else ''
        self.standardOutputFile = stc.stdout_file
        self.standardErrorFile = stc.stderr_file
        self.execute = stc.execute
        self.arguments = stc.arguments

        outputLock = threading.Lock()

        # Check if filterSubDir has been overridden for this Transfer/SIP
        try:
            var = UnitVariable.objects.get(unittype=self.unit.unitType,
                                           unituuid=self.unit.UUID,
                                           variable=self.execute)
        except (UnitVariable.DoesNotExist, UnitVariable.MultipleObjectsReturned):
            var = None

        if var:
            try:
                variableValue = ast.literal_eval(var.variablevalue)
            except SyntaxError:
                # SyntaxError = contents of variableValue weren't the expected dict
                pass
            else:
                filterSubDir = variableValue['filterSubDir']

        SIPReplacementDic = unit.getReplacementDic(unit.currentPath)
        # Escape all values for shell
        for key, value in SIPReplacementDic.items():
            SIPReplacementDic[key] = archivematicaFunctions.escapeForCommand(value)
        self.taskGroupsLock.acquire()

        currentTaskGroup = None

        for file, fileUnit in unit.fileList.items():
            if filterFileEnd:
                if not file.endswith(filterFileEnd):
                    continue
            if filterFileStart:
                if not os.path.basename(file).startswith(filterFileStart):
                    continue
            if filterSubDir:
                if not file.startswith(unit.pathString + filterSubDir):
                    continue

            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            arguments = self.arguments

            # Apply passvar replacement values
            if self.jobChainLink.passVar is not None:
                if isinstance(self.jobChainLink.passVar, list):
                    for passVar in self.jobChainLink.passVar:
                        if isinstance(passVar, ReplacementDict):
                            arguments, standardOutputFile, standardErrorFile = passVar.replace(arguments, standardOutputFile, standardErrorFile)
                elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                    arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(arguments, standardOutputFile, standardErrorFile)

            # Apply file replacement values
            commandReplacementDic = fileUnit.getReplacementDic()
            for key, value in commandReplacementDic.items():
                # Escape values for shell
                commandReplacementDic[key] = archivematicaFunctions.escapeForCommand(value)
            arguments, standardOutputFile, standardErrorFile = commandReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

            # Apply unit (SIP/Transfer) replacement values
            arguments, standardOutputFile, standardErrorFile = SIPReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

            if currentTaskGroup is None or currentTaskGroup.count() > BATCH_SIZE:
                currentTaskGroup = TaskGroup(self, self.execute)
                self.taskGroups[currentTaskGroup.UUID] = currentTaskGroup

            currentTaskGroup.addTask(
                arguments, standardOutputFile, standardErrorFile,
                outputLock, commandReplacementDic)

        for taskGroup in self.taskGroups.values():
            taskGroup.logTaskCreatedSQL()
            TaskGroupRunner.runTaskGroup(taskGroup, self.taskGroupFinished)

        self.clearToNextLink = True
        self.taskGroupsLock.release()

        # If the batch of files was empty, we can immediately proceed to the
        # next job in the chain.  Assume a successful status code.
        if self.taskGroups == {}:
            self.jobChainLink.linkProcessingComplete(0)

    def taskGroupFinished(self, finishedTaskGroup):
        finishedTaskGroup.write_output()

        # Exit code is the maximum of all task groups (and each task group's
        # exit code is the maximum of the tasks it contains... turtles all the
        # way down)
        self.exitCode = max([finishedTaskGroup.calculateExitCode(), self.exitCode])

        self.taskGroupsLock.acquire()
        if finishedTaskGroup.UUID in self.taskGroups:
            del self.taskGroups[finishedTaskGroup.UUID]
        else:
            # Shouldn't happen!
            LOGGER.warning('TaskGroup UUID %s not in task list %s', finishedTaskGroup.UUID, self.taskGroups)

        if self.clearToNextLink is True and self.taskGroups == {}:
            # All TaskGroups have been processed.  Proceed to next job in the chain.
            LOGGER.debug('Proceeding to next link %s', self.jobChainLink.UUID)
            self.jobChainLink.linkProcessingComplete(self.exitCode, self.jobChainLink.passVar)

        self.taskGroupsLock.release()
