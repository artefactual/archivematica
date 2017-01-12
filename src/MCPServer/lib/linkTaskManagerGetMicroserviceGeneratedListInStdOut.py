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

import logging
import os
import threading

from archivematicaFunctions import escapeForCommand
from dicts import ChoicesDict, ReplacementDict
from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard

LOGGER = logging.getLogger('archivematica.mcp.server')


class linkTaskManagerGetMicroserviceGeneratedListInStdOut(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerGetMicroserviceGeneratedListInStdOut, self).__init__(jobChainLink)

        config = self.get_config()

        filterSubDir = config.filterSubdir
        standardOutputFile = config.stdoutFile
        standardErrorFile = config.stderrFile
        execute = config.execute
        self.execute = execute
        arguments = config.arguments

        # Apply passvar replacement values
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        arguments, standardOutputFile, standardErrorFile = passVar.replace(arguments, standardOutputFile, standardErrorFile)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(arguments, standardOutputFile, standardErrorFile)

        # Apply unit (SIP/Transfer) replacement values
        directory = os.path.join(self.unit.currentPath, filterSubDir) if filterSubDir else self.unit.currentPath
        commandReplacementDic = self.unit.getReplacementDic(directory)

        # Escape all values for shell
        for key, value in commandReplacementDic.items():
                commandReplacementDic[key] = escapeForCommand(value)
        arguments, standardOutputFile, standardErrorFile = commandReplacementDic.replace(arguments, standardOutputFile, standardErrorFile)

        self.task = taskStandard(self, execute, arguments, standardOutputFile, standardErrorFile, UUID=self.UUID)
        self.log_task(commandReplacementDic, self.UUID, arguments)
        t = threading.Thread(target=self.task.performTask)
        t.daemon = True
        t.start()

    def get_config(self):
        return self.link.config.standard

    def task_completed_callback(self, uuid, results):
        """
        This callback is triggered by the taskStandard once the Gearman job
        completes.
        """
        self.log_completed_task(uuid, results)

        try:
            choices = ChoicesDict.fromstring(results["stdOut"])
        except Exception:
            LOGGER.exception('Unable to create dic from output %s', results['stdOut'])
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

        self.jobChainLink.linkProcessingComplete(results["exitCode"], self.jobChainLink.passVar)
