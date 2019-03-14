"""Collection of tasks that we'll send off to the MCPClient (via Gearman)."""

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

import threading
import databaseFunctions
import uuid
import cPickle
import logging
import os

from databaseFunctions import getUTCDate
from main.models import Task

from django.db import transaction
from django.utils import six, timezone

LOGGER = logging.getLogger("archivematica.mcp.server.taskGroup")


class TaskGroup:
    def __init__(self, linkTaskManager, execute):
        self.linkTaskManager = linkTaskManager
        self.execute = execute.encode("utf-8")
        self.UUID = str(uuid.uuid4())

        self.finalised = False

        self.groupTasks = []
        self.groupTasksLock = threading.Lock()

    def unit_uuid(self):
        return self.linkTaskManager.unit.UUID

    def name(self):
        return self.execute.lower()

    def addTask(
        self,
        arguments,
        standardOutputFile,
        standardErrorFile,
        outputLock=threading.Lock(),
        commandReplacementDic={},
        wants_output=False,
    ):
        """Add a task to this group"""
        with self.groupTasksLock:
            if self.finalised:
                raise Exception("Cannot add a task to a finalized TaskGroup")

            self.groupTasks.append(
                self.Task(
                    arguments,
                    standardOutputFile,
                    standardErrorFile,
                    outputLock,
                    commandReplacementDic,
                    wants_output,
                )
            )

    def count(self):
        """The number of tasks in this group"""
        with self.groupTasksLock:
            return len(self.groupTasks)

    def tasks(self):
        """The tasks in this group."""
        return self.groupTasks

    def logTaskCreatedSQL(self):
        """Log task creation times for this group of tasks."""
        with self.groupTasksLock:
            self.finalised = True

            def insertTasks():
                with transaction.atomic():
                    for task in self.groupTasks:
                        self._log_task(
                            self.linkTaskManager,
                            task.commandReplacementDic,
                            task.UUID,
                            task.arguments,
                        )

            databaseFunctions.retryOnFailure("Insert tasks", insertTasks)

    def _log_task(self, taskManager, commandReplacementDic, taskUUID, arguments):
        """
        Creates a new entry in the Tasks table using the supplied data.

        :param MCPServer.linkTaskManager taskManager: A linkTaskManager subclass instance.
        :param ReplacementDict commandReplacementDic: A ReplacementDict or dict instance. %fileUUID% and %relativeLocation% variables will be looked up from this dict.
        :param str taskUUID: The UUID to be used for this Task in the database.
        :param str arguments: The arguments to be passed to the command when it is executed, as a string. Can contain replacement variables; see ReplacementDict for supported values.
        """
        jobUUID = taskManager.jobChainLink.UUID
        fileUUID = ""
        if "%fileUUID%" in commandReplacementDic:
            fileUUID = commandReplacementDic["%fileUUID%"]
        taskexec = taskManager.execute
        fileName = os.path.basename(
            os.path.abspath(commandReplacementDic["%relativeLocation%"])
        )

        Task.objects.create(
            taskuuid=taskUUID,
            job_id=jobUUID,
            fileuuid=fileUUID,
            filename=fileName,
            execution=taskexec,
            arguments=arguments,
            createdtime=getUTCDate(),
        )

    def calculateExitCode(self):
        """
        The exit code for this task group (defined as the largest exit code of any of
        its tasks)
        """
        result = 0

        for task in self.groupTasks:
            if task.results["exitCode"] > result:
                result = task.results["exitCode"]

        return result

    def serialize(self):
        """
        Serialize this TaskGroup into something suitable for MCP Client.
        """
        result = {"tasks": {}}

        for task in self.groupTasks:
            task_data = {}
            task_data["uuid"] = task.UUID
            task_data["createdDate"] = timezone.now().isoformat(" ")
            task_data["arguments"] = task.arguments
            task_data["wants_output"] = task.wants_output

            result["tasks"][task.UUID] = task_data

        return cPickle.dumps(result)

    def _write_file_to_disk(self, path, contents):
        """Write the bytes in ``contents`` to ``path`` in append mode.

        The mode of ``path`` is adjusted to ensure that it's not readable by
        ``others``.
        """
        if not all((path, contents)):
            return
        try:
            with open(path, "a") as f:
                f.write(contents)
            os.chmod(path, 0o750)
        except Exception as err:
            LOGGER.warning("Unable to write to: %s: %s", path, err)

    def write_output(self):
        """
        Write the stdout/stderror we got from MCP Client out to files if
        necessary.
        """
        for task in self.groupTasks:
            with task.outputLock:
                self._write_file_to_disk(
                    task.standardOutputFile, six.binary_type(task.results["stdout"])
                )
                self._write_file_to_disk(
                    task.standardErrorFile, six.binary_type(task.results["stderror"])
                )

    class Task:
        """
        Captures the detail of a single task.  The `results` map is filled out by
        TaskGroupRunner on completion of the task.
        """

        def __init__(
            self,
            arguments,
            standardOutputFile,
            standardErrorFile,
            outputLock,
            commandReplacementDic,
            wants_output,
        ):
            self.arguments = arguments
            self.standardOutputFile = standardOutputFile
            self.standardErrorFile = standardErrorFile
            self.outputLock = outputLock
            self.UUID = str(uuid.uuid4())
            self.commandReplacementDic = commandReplacementDic

            self.wants_output = any(
                (wants_output, standardOutputFile, standardErrorFile)
            )

            self.results = {"exitCode": 0, "stdout": "", "stderror": ""}
