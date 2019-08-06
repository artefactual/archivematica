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
import threading

from django.conf import settings as django_settings

from linkTaskManager import LinkTaskManager
import archivematicaFunctions
from dicts import ReplacementDict
from main.models import UnitVariable

import metrics
from taskGroupRunner import TaskGroupRunner
from taskGroup import TaskGroup

LOGGER = logging.getLogger("archivematica.mcp.server")

# The number of files we'll pack into each MCP Client job.  Chosen somewhat
# arbitrarily, but benchmarking with larger values (like 512) didn't make much
# difference to throughput.
#
# Setting this too large will use more memory; setting it too small will hurt
# throughput.  So the trick is to set it juuuust right.
BATCH_SIZE = django_settings.BATCH_SIZE


class linkTaskManagerFiles(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerFiles, self).__init__(jobChainLink, unit)

        # The list of task groups we'll be executing for this batch of files
        self.taskGroupsLock = threading.Lock()
        self.taskGroups = {}

        # Zero if every taskGroup executed so far has succeeded.  Otherwise,
        # something greater than zero.
        self.exitCode = 0

        self.clearToNextLink = False

        config = self.jobChainLink.link.config
        # These three may be concatenated/compared with other strings,
        # so they need to be bytestrings here
        filterFileEnd = (
            str(config["filter_file_end"]) if config["filter_file_end"] else ""
        )
        filterFileStart = (
            str(config["filter_file_start"]) if config["filter_file_start"] else ""
        )
        filterSubDir = str(config["filter_subdir"]) if config["filter_subdir"] else ""
        self.standardOutputFile = config["stdout_file"]
        self.standardErrorFile = config["stderr_file"]
        self.execute = config["execute"]
        self.arguments = config["arguments"]

        # Used by ``TaskGroup._log_task``.
        self.execute = config["execute"]

        outputLock = threading.Lock()

        # Check if filterSubDir has been overridden for this Transfer/SIP
        try:
            var = UnitVariable.objects.get(
                unittype=self.unit.UNIT_VARIABLE_TYPE,
                unituuid=self.unit.uuid,
                variable=self.execute,
            )
        except (UnitVariable.DoesNotExist, UnitVariable.MultipleObjectsReturned):
            var = None

        if var:
            try:
                variableValue = ast.literal_eval(var.variablevalue)
            except SyntaxError:
                # SyntaxError = contents of variableValue weren't the expected dict
                pass
            else:
                filterSubDir = variableValue["filterSubDir"]

        SIPReplacementDic = unit.get_replacement_mapping()
        # Escape all values for shell
        for key, value in SIPReplacementDic.items():
            SIPReplacementDic[key] = archivematicaFunctions.escapeForCommand(value)

        with metrics.task_group_lock_summary.labels(function="__init__").time():
            self.taskGroupsLock.acquire()

        currentTaskGroup = None

        for fileReplacements in unit.files(
            filter_filename_start=filterFileStart,
            filter_filename_end=filterFileEnd,
            filter_subdir=filterSubDir,
        ):
            standardOutputFile = self.standardOutputFile
            standardErrorFile = self.standardErrorFile
            arguments = self.arguments

            # File replacement values take priority
            commandReplacementDic = SIPReplacementDic.copy()
            commandReplacementDic.update(fileReplacements)

            # Apply file replacement values
            for key, value in commandReplacementDic.items():
                # Escape values for shell
                escapedValue = archivematicaFunctions.escapeForCommand(value)
                if arguments is not None:
                    arguments = arguments.replace(key, escapedValue)
                if standardOutputFile is not None:
                    standardOutputFile = standardOutputFile.replace(key, escapedValue)
                if standardErrorFile is not None:
                    standardErrorFile = standardErrorFile.replace(key, escapedValue)

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

            if currentTaskGroup is None or currentTaskGroup.count() > BATCH_SIZE:
                currentTaskGroup = TaskGroup(self, self.execute)
                self.taskGroups[currentTaskGroup.UUID] = currentTaskGroup

            currentTaskGroup.addTask(
                arguments,
                standardOutputFile,
                standardErrorFile,
                outputLock,
                commandReplacementDic,
            )

        for taskGroup in self.taskGroups.values():
            taskGroup.logTaskCreatedSQL()
            TaskGroupRunner.runTaskGroup(taskGroup, self.taskGroupFinished)

        self.clearToNextLink = True
        self.taskGroupsLock.release()

        # If the batch of files was empty, we can immediately proceed to the
        # next job in the chain.  Assume a successful status code.
        if self.taskGroups == {}:
            self.jobChainLink.on_complete(0)

    def taskGroupFinished(self, finishedTaskGroup):
        finishedTaskGroup.write_output()

        # Exit code is the maximum of all task groups (and each task group's
        # exit code is the maximum of the tasks it contains... turtles all the
        # way down)
        self.exitCode = max([finishedTaskGroup.calculateExitCode(), self.exitCode])

        with metrics.task_group_lock_summary.labels(
            function="taskGroupFinished"
        ).time():
            self.taskGroupsLock.acquire()

        if finishedTaskGroup.UUID in self.taskGroups:
            del self.taskGroups[finishedTaskGroup.UUID]
        else:
            # Shouldn't happen!
            LOGGER.warning(
                "TaskGroup UUID %s not in task list %s",
                finishedTaskGroup.UUID,
                self.taskGroups,
            )

        if self.clearToNextLink is True and self.taskGroups == {}:
            # All TaskGroups have been processed.  Proceed to next job in the chain.
            LOGGER.debug("Proceeding to next link %s", self.jobChainLink.uuid)
            self.jobChainLink.on_complete(self.exitCode, self.jobChainLink.pass_var)

        self.taskGroupsLock.release()
