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

import cPickle
import gearman
import logging
import os
import threading
import time
import uuid

from utils import log_exceptions

from django.conf import settings as django_settings
from django.utils import timezone

from databaseFunctions import auto_close_db
from fileOperations import writeToFile

LOGGER = logging.getLogger('archivematica.mcp.server')

# ~Class Task~
# Tasks are what are assigned to clients.
# They have a zero-many(tasks) TO one(job) relationship
# This relationship is formed by storing a pointer to it's owning job in its job variable.
# They use a "replacement dictionary" to define variables for this task.
# Variables used for the task are defined in the Job's configuration/module (The xml file)


limitGearmanConnectionsSemaphore = threading.Semaphore(value=django_settings.LIMIT_GEARMAN_CONNS)


class taskStandard():
    """A task to hand to gearman"""

    def __init__(self, linkTaskManager, execute, arguments, standardOutputFile,
                 standardErrorFile, outputLock=None, UUID=None,
                 alwaysCapture=False):
        if UUID is None:
            UUID = uuid.uuid4().__str__()
        self.UUID = UUID
        self.linkTaskManager = linkTaskManager
        self.execute = execute.encode("utf-8")
        self.arguments = arguments
        self.standardOutputFile = standardOutputFile
        self.standardErrorFile = standardErrorFile
        self.outputLock = outputLock
        self.alwaysCapture = alwaysCapture

    @log_exceptions
    @auto_close_db
    def performTask(self):
        limitGearmanConnectionsSemaphore.acquire()
        gm_client = gearman.GearmanClient([django_settings.GEARMAN_SERVER])
        data = {"createdDate": timezone.now().isoformat(' ')}
        data["arguments"] = self.arguments
        data["alwaysCapture"] = self.alwaysCapture  # tells worker to always capture stdout
        LOGGER.info('Executing %s %s', self.execute, data)
        completed_job_request = None
        failMaxSleep = 60
        failSleepInitial = 1
        failSleep = failSleepInitial
        failSleepIncrementor = 2
        while completed_job_request is None:
            try:
                completed_job_request = gm_client.submit_job(
                    self.execute.lower(), cPickle.dumps(data), self.UUID)
            except gearman.errors.ServerUnavailable:
                completed_job_request = None
                time.sleep(failSleep)
                if failSleep == failSleepInitial:
                    LOGGER.exception('Error submitting job. Retrying.')
                if failSleep < failMaxSleep:
                    failSleep += failSleepIncrementor
        limitGearmanConnectionsSemaphore.release()
        self.check_request_status(completed_job_request)
        gm_client.shutdown()
        LOGGER.debug('Finished performing task %s', self.UUID)

    def check_request_status(self, job_request):
        if job_request.complete:
            self.results = cPickle.loads(job_request.result)
            LOGGER.debug('Task %s finished! Result %s - %s', job_request.job.unique, job_request.state, self.results)
            self.writeOutputs()
            self.linkTaskManager.taskCompletedCallBackFunction(self)
        elif job_request.timed_out:
            LOGGER.error('Task %s timed out!', job_request.unique)
            self.results['exitCode'] = -1
            self.results["stdError"] = "Task %s timed out!" % job_request.unique
            self.linkTaskManager.taskCompletedCallBackFunction(self)

        elif job_request.state == gearman.client.JOB_UNKNOWN:
            LOGGER.error('Task %s connection failed!', job_request.unique)
            self.results["stdError"] = "Task %s connection failed!" % job_request.unique
            self.results['exitCode'] = -1
            self.linkTaskManager.taskCompletedCallBackFunction(self)
        else:
            LOGGER.error('Task %s failed!', job_request.unique)
            self.results["stdError"] = "Task %s failed!" % job_request.unique
            self.results['exitCode'] = -1
            self.linkTaskManager.taskCompletedCallBackFunction(self)

    def outputFileIsWritable(self, fileName):
        """
        Validates whether a given file is writeable or, if the file does not exist, whether its parent directory is writeable.
        """
        if os.path.exists(fileName):
            target = fileName
        else:
            target = os.path.dirname(fileName)
        return os.access(target, os.W_OK)

    def validateOutputFile(self, fileName):
        """
        Returns True if the given file is writeable.
        If the passed file is not None and isn't writeable, logs the filename.
        """
        if fileName is None:
            return False

        if not self.outputFileIsWritable(fileName):
            LOGGER.warning('Unable to write to file %s', fileName)
            return False

        return True

    # Used to write the output of the commands to the specified files
    def writeOutputs(self):
        """Used to write the output of the commands to the specified files"""

        if self.outputLock is not None:
            self.outputLock.acquire()

        if self.validateOutputFile(self.standardOutputFile):
            stdoutStatus = writeToFile(self.results["stdOut"], self.standardOutputFile)
        else:
            stdoutStatus = -1
        if self.validateOutputFile(self.standardErrorFile):
            stderrStatus = writeToFile(self.results["stdError"], self.standardErrorFile)
        else:
            stderrStatus = -1

        if self.outputLock is not None:
            self.outputLock.release()

        if stdoutStatus and self.standardOutputFile is not None:
            if isinstance(self.standardOutputFile, unicode):
                stdout = self.standardOutputFile.encode('utf-8')
            else:
                stdout = self.standardOutputFile
            self.stdError = "Failed to write to file{" + stdout + "}\r\n" + self.results["stdOut"]
        if stderrStatus and self.standardErrorFile is not None:
            if isinstance(self.standardErrorFile, unicode):
                stderr = self.standardErrorFile.encode('utf-8')
            else:
                stderr = self.standardErrorFile
            self.stdError = "Failed to write to file{" + stderr + "}\r\n" + self.results["stdError"]
        if self.results['exitCode']:
            return self.results['exitCode']
        return stdoutStatus + stderrStatus
