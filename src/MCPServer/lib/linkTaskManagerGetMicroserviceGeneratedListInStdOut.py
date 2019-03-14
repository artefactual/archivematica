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
import logging
import os

# This project,  alphabetical by import source
from linkTaskManager import LinkTaskManager
import archivematicaFunctions
from dicts import ChoicesDict, ReplacementDict

from taskGroup import TaskGroup
from taskGroupRunner import TaskGroupRunner

LOGGER = logging.getLogger("archivematica.mcp.server")


class linkTaskManagerGetMicroserviceGeneratedListInStdOut(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerGetMicroserviceGeneratedListInStdOut, self).__init__(
            jobChainLink, unit
        )
        config = self.jobChainLink.link.config
        filterSubDir = config["filter_subdir"]
        standardOutputFile = config["stdout_file"]
        standardErrorFile = config["stderr_file"]
        execute = config["execute"]
        arguments = config["arguments"]

        # Used by ``TaskGroup._log_task``.
        self.execute = config["execute"]

        if filterSubDir:
            directory = os.path.join(unit.currentPath, filterSubDir)
        else:
            directory = unit.currentPath

        # Apply passvar replacement values
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        arguments, standardOutputFile, standardErrorFile = passVar.replace(
                            arguments, standardOutputFile, standardErrorFile
                        )
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(
                    arguments, standardOutputFile, standardErrorFile
                )

        # Apply unit (SIP/Transfer) replacement values
        commandReplacementDic = unit.getReplacementDic(directory)
        # Escape all values for shell
        for key, value in commandReplacementDic.items():
            commandReplacementDic[key] = archivematicaFunctions.escapeForCommand(value)
        arguments, standardOutputFile, standardErrorFile = commandReplacementDic.replace(
            arguments, standardOutputFile, standardErrorFile
        )

        group = TaskGroup(self, execute)
        group.addTask(
            arguments,
            standardOutputFile,
            standardErrorFile,
            commandReplacementDic=commandReplacementDic,
            wants_output=True,
        )
        group.logTaskCreatedSQL()
        TaskGroupRunner.runTaskGroup(group, self.taskGroupFinished)

    def taskGroupFinished(self, finishedTaskGroup):
        finishedTaskGroup.write_output()

        stdout = None
        tasks = finishedTaskGroup.tasks()
        try:
            stdout = tasks[0].results["stdout"]
        except KeyError:
            pass
        LOGGER.debug("stdout emitted by client: %s", stdout)

        try:
            choices = ChoicesDict.fromstring(stdout)
        except Exception:
            LOGGER.exception("Unable to create dic from output %s", stdout)
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

        self.jobChainLink.linkProcessingComplete(
            finishedTaskGroup.calculateExitCode(), self.jobChainLink.passVar
        )
