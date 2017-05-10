#!/usr/bin/env python2

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
import time
import uuid

from archivematicaFunctions import escapeForCommand
from archivematicaMCP import limitTaskThreads, limitTaskThreadsSleep
from dicts import ReplacementDict
from linkTaskManager import LinkTaskManager
from main.models import UnitVariable
from taskStandard import taskStandard

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerFiles(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerFiles, self).__init__(jobChainLink)

        self.tasks = {}
        self.tasksLock = threading.Lock()
        self.exitCode = 0
        self.clearToNextLink = False

        config = self.get_config()

        # These three may be concatenated/compared with other strings,
        # so they need to be bytestrings here
        filterFileEnd = str(config.filterFileEnd) if config.filterFileEnd else ''
        filterFileStart = str(config.filterFileStart) if config.filterFileStart else ''
        filterSubDir = str(config.filterSubdir) if config.filterSubdir else ''
        self.standardOutputFile = config.stdoutFile
        self.standardErrorFile = config.stderrFile
        self.execute = config.execute
        self.arguments = config.arguments

        outputLock = threading.Lock() if config.requiresOutputLock else None

        # Check if filterSubDir has been overridden for this Transfer/SIP
        try:
            var = UnitVariable.objects.get(unittype=self.unit.unitType, unituuid=self.unit.UUID, variable=self.execute)
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

        SIPReplacementDic = self.unit.getReplacementDic(self.unit.currentPath)
        # Escape all values for shell
        for key, value in SIPReplacementDic.items():
            SIPReplacementDic[key] = escapeForCommand(value)
        self.tasksLock.acquire()
        for file, fileUnit in self.unit.fileList.items():
            if filterFileEnd:
                if not file.endswith(filterFileEnd):
                    continue
            if filterFileStart:
                if not os.path.basename(file).startswith(filterFileStart):
                    continue
            if filterSubDir:
                if not file.startswith(self.unit.pathString + filterSubDir):
                    continue

            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            execute = self.execute
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
                commandReplacementDic[key] = escapeForCommand(value)
            arguments, standardOutputFile, standardErrorFile = commandReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

            # Apply unit (SIP/Transfer) replacement values
            arguments, standardOutputFile, standardErrorFile = SIPReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

            UUID = str(uuid.uuid4())
            task = taskStandard(self, execute, arguments, standardOutputFile, standardErrorFile, outputLock=outputLock, UUID=UUID)
            self.tasks[UUID] = task
            self.log_task(commandReplacementDic, UUID, arguments)
            t = threading.Thread(target=task.performTask)
            t.daemon = True
            while(limitTaskThreads <= threading.activeCount()):
                self.tasksLock.release()
                time.sleep(limitTaskThreadsSleep)
                self.tasksLock.acquire()
            t.start()

        self.clearToNextLink = True
        self.tasksLock.release()
        if not self.tasks:
            self.jobChainLink.linkProcessingComplete(self.exitCode)

    def get_config(self):
        return self.link.config.standard

    def task_completed_callback(self, uuid, results):
        """
        This callback is triggered by the taskStandard once the Gearman job
        completes.
        """
        self.log_completed_task(uuid, results)

        self.exitCode = max(self.exitCode, abs(results['exitCode']))

        with self.tasksLock:
            if uuid in self.tasks:
                del self.tasks[uuid]
            else:
                LOGGER.warning('Task UUID %s not in task list %s', uuid, self.tasks)
                exit(1)

            if self.clearToNextLink is True and not self.tasks:
                LOGGER.debug('Proceeding to next link %s', self.jobChainLink.UUID)
                self.jobChainLink.linkProcessingComplete(self.exitCode, self.jobChainLink.passVar)
