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

        # Apply passvar replacement values
        if self.jobChainLink.pass_var is not None:
            if isinstance(self.jobChainLink.pass_var, list):
                for passVar in self.jobChainLink.pass_var:
                    if isinstance(passVar, ReplacementDict):
                        arguments, standardOutputFile, standardErrorFile = passVar.replace(
                            arguments, standardOutputFile, standardErrorFile
                        )
            elif isinstance(self.jobChainLink.pass_var, ReplacementDict):
                arguments, standardOutputFile, standardErrorFile = self.jobChainLink.pass_var.replace(
                    arguments, standardOutputFile, standardErrorFile
                )

        # Apply unit (SIP/Transfer) replacement values
        commandReplacementDic = unit.get_replacement_mapping(
            filter_subdir_path=filterSubDir
        )
        # Escape all values for shell
        for key, value in commandReplacementDic.items():
            escapedValue = archivematicaFunctions.escapeForCommand(value)
            if arguments is not None:
                arguments = arguments.replace(key, escapedValue)
            if standardOutputFile is not None:
                standardOutputFile = standardOutputFile.replace(key, escapedValue)
            if standardErrorFile is not None:
                standardErrorFile = standardErrorFile.replace(key, escapedValue)

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
        if self.jobChainLink.pass_var is not None:
            if isinstance(self.jobChainLink.pass_var, list):
                for index, value in enumerate(self.jobChainLink.pass_var):
                    if isinstance(value, ChoicesDict):
                        self.jobChainLink.pass_var[index] = choices
                        break
                else:
                    self.jobChainLink.pass_var.append(choices)
            else:
                self.jobChainLink.pass_var = [choices, self.jobChainLink.pass_var]
        else:
            self.jobChainLink.pass_var = [choices]

        self.jobChainLink.on_complete(
            finishedTaskGroup.calculateExitCode(), self.jobChainLink.pass_var
        )
