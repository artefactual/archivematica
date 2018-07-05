#!/usr/bin/env python2

"""
A collection of tasks that we'll send off to the MCP Client (via Gearman).
"""


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

from fileOperations import writeToFile

from django.db import transaction
from django.utils import timezone

LOGGER = logging.getLogger('archivematica.mcp.server.taskGroup')


class TaskGroup():

    def __init__(self, linkTaskManager, execute):
        self.linkTaskManager = linkTaskManager
        self.execute = execute.encode("utf-8")
        self.UUID = str(uuid.uuid4())

        self.finalised = False

        self.groupTasks = []
        self.groupTasksLock = threading.Lock()

    def name(self):
        return self.execute.lower()

    def addTask(self,
                arguments, standardOutputFile, standardErrorFile,
                outputLock=threading.Lock(),
                commandReplacementDic={}):
        """Add a task to this group"""
        with self.groupTasksLock:
            if self.finalised:
                raise Exception("Cannot add a task to a finalized TaskGroup")

            self.groupTasks.append(self.Task(arguments,
                                             standardOutputFile, standardErrorFile,
                                             outputLock,
                                             commandReplacementDic))

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

            with transaction.atomic():
                for task in self.groupTasks:
                    databaseFunctions.logTaskCreatedSQL(self.linkTaskManager,
                                                        task.commandReplacementDic,
                                                        task.UUID,
                                                        task.arguments)

    def calculateExitCode(self):
        """
        The exit code for this task group (defined as the largest exit code of any of
        its tasks)
        """
        result = 0

        for task in self.groupTasks:
            if task.results['exitCode'] > result:
                result = task.results['exitCode']

        return result

    def serialize(self):
        """
        Serialize this TaskGroup into something suitable for MCP Client.
        """
        result = {'tasks': {}}

        for task in self.groupTasks:
            task_data = {}
            task_data["uuid"] = task.UUID
            task_data["createdDate"] = timezone.now().isoformat(' ')
            task_data["arguments"] = task.arguments
            task_data["wants_output"] = bool(task.standardOutputFile or task.standardErrorFile)

            result['tasks'][task.UUID] = task_data

        return cPickle.dumps(result)

    def write_output(self):
        """
        Write the stdout/stderror we got from MCP Client out to files if
        necessary.
        """
        for task in self.groupTasks:
            with task.outputLock:
                if task.standardOutputFile:
                    try:
                        writeToFile(task.results['stdout'], task.standardOutputFile)
                    except Exception as e:
                        LOGGER.warning("Unable to write to: %s: %s", task.standardOutputFile, str(e))
                        LOGGER.exception(e)

                if task.standardErrorFile:
                    try:
                        writeToFile(task.results['stderror'], task.standardErrorFile)
                    except Exception as e:
                        LOGGER.warning("Unable to write to: %s: %s", task.standardErrorFile, str(e))
                        LOGGER.exception(e)

    class Task():
        """
        Captures the detail of a single task.  The `results` map is filled out by
        TaskGroupRunner on completion of the task.
        """
        def __init__(self,
                     arguments,
                     standardOutputFile, standardErrorFile,
                     outputLock,
                     commandReplacementDic):
            self.arguments = arguments
            self.standardOutputFile = standardOutputFile
            self.standardErrorFile = standardErrorFile
            self.outputLock = outputLock
            self.UUID = str(uuid.uuid4())
            self.commandReplacementDic = commandReplacementDic

            self.results = {
                'exitCode': 0,
                'stdout': '',
                'stderror': '',
            }
