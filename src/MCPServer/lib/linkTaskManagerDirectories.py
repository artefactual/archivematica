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

import os
import threading

from archivematicaFunctions import escapeForCommand
from dicts import ReplacementDict
from linkTaskManager import LinkTaskManager
from taskStandard import taskStandard


class linkTaskManagerDirectories(LinkTaskManager):
    def __init__(self, jobChainLink):
        super(linkTaskManagerDirectories, self).__init__(jobChainLink)

        config = self.get_config()

        arguments = config.arguments
        stdout_file = config.stdoutFile
        stderr_file = config.stderrFile

        # Apply passvar replacement values
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        arguments, stdout_file, stderr_file = passVar.replace(arguments, stdout_file, stdout_file)
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                arguments, stdout_file, stderr_file = self.jobChainLink.passVar.replace(arguments, stdout_file, stderr_file)

        # Apply unit (SIP/Transfer) replacement values
        directory = os.path.join(self.unit.currentPath, config.filterSubdir) if config.filterSubdir else self.unit.currentPath
        commandReplacementDic = self.unit.getReplacementDic(directory)

        # Escape all values for shell
        for key, value in commandReplacementDic.items():
            commandReplacementDic[key] = escapeForCommand(value)
        arguments, stdout_file, stderr_file = commandReplacementDic.replace(arguments, stdout_file, stderr_file)

        # Execute Gearman client in a different thread
        self.task = taskStandard(self, config.execute, arguments, stdout_file, stderr_file, UUID=self.UUID)
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
        self.jobChainLink.linkProcessingComplete(results["exitCode"], self.jobChainLink.passVar)
