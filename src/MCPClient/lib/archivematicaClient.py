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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>

# ~DOC~
#
# --- This is the MCP Client---
# It connects to the MCP server, and informs the server of the tasks it can perform.
# The server can send a command (matching one of the tasks) for the client to perform.
# The client will perform that task, and return the exit code and output to the server.
#
# For archivematica 0.9 release. Added integration with the transcoder.
# The server will send the transcoder association pk, and file uuid to run.
# The client is responsible for running the correct command on the file.

import ConfigParser
import cPickle
import gearman
import logging
import os
import time
from socket import gethostname
import threading
import traceback

import django
django.setup()

from django.conf import settings as django_settings

from main.models import Task

from databaseFunctions import auto_close_db, getUTCDate
from executeOrRunSubProcess import executeOrRun


logger = logging.getLogger('archivematica.mcp.client')

replacementDic = {
    "%sharedPath%": django_settings.SHARED_DIRECTORY,
    "%clientScriptsDirectory%": django_settings.CLIENT_SCRIPTS_DIRECTORY,
    "%clientAssetsDirectory%": django_settings.CLIENT_ASSETS_DIRECTORY,
}
supportedModules = {}


def loadSupportedModulesSupport(key, value):
    for key2, value2 in replacementDic.items():
        value = value.replace(key2, value2)
    if not os.path.isfile(value):
        logger.error("Warning! Module can't find file, or relies on system path: {%s} %s", key, value)
    supportedModules[key] = value + " "


def loadSupportedModules(file):
    supportedModulesConfig = ConfigParser.RawConfigParser()
    supportedModulesConfig.read(file)
    for key, value in supportedModulesConfig.items('supportedCommands'):
        loadSupportedModulesSupport(key, value)

    if django_settings.LOAD_SUPPORTED_COMMANDS_SPECIAL:
        for key, value in supportedModulesConfig.items('supportedCommandsSpecial'):
            loadSupportedModulesSupport(key, value)


@auto_close_db
def executeCommand(gearman_worker, gearman_job):
    try:
        execute = gearman_job.task
        logger.info('Executing %s (%s)', execute, gearman_job.unique)
        data = cPickle.loads(gearman_job.data)
        utcDate = getUTCDate()
        arguments = data["arguments"]  # .encode("utf-8")
        if isinstance(arguments, unicode):
            arguments = arguments.encode("utf-8")

        sInput = ""
        clientID = gearman_worker.worker_client_id

        task = Task.objects.get(taskuuid=gearman_job.unique)
        if task.starttime is not None:
            exitCode = -1
            stdOut = ""
            stdError = """Detected this task has already started!
Unable to determine if it completed successfully."""
            return cPickle.dumps({"exitCode": exitCode, "stdOut": stdOut, "stdError": stdError})
        else:
            task.client = clientID
            task.starttime = utcDate
            task.save()

        if execute not in supportedModules:
            output = ["Error!", "Error! - Tried to run and unsupported command."]
            exitCode = -1
            return cPickle.dumps({"exitCode": exitCode, "stdOut": output[0], "stdError": output[1]})
        command = supportedModules[execute]

        replacementDic["%date%"] = utcDate.isoformat()
        replacementDic["%jobCreatedDate%"] = data["createdDate"]
        # Replace replacement strings
        for key in replacementDic.keys():
            command = command.replace(key, replacementDic[key])
            arguments = arguments.replace(key, replacementDic[key])

        key = "%taskUUID%"
        value = gearman_job.unique.__str__()
        arguments = arguments.replace(key, value)

        # Execute command
        command += " " + arguments
        logger.info('<processingCommand>{%s}%s</processingCommand>', gearman_job.unique, command)
        exitCode, stdOut, stdError = executeOrRun("command", command, sInput, printing=True)
        return cPickle.dumps({"exitCode": exitCode, "stdOut": stdOut, "stdError": stdError})
    except OSError:
        logger.exception('Execution failed')
        output = ["Archivematica Client Error!", traceback.format_exc()]
        exitCode = 1
        return cPickle.dumps({"exitCode": exitCode, "stdOut": output[0], "stdError": output[1]})
    except Exception:
        logger.exception('Unexpected error')
        output = ["", traceback.format_exc()]
        return cPickle.dumps({"exitCode": -1, "stdOut": output[0], "stdError": output[1]})


@auto_close_db
def startThread(threadNumber):
    """Setup a gearman client, for the thread."""
    gm_worker = gearman.GearmanWorker([django_settings.GEARMAN_SERVER])
    hostID = gethostname() + "_" + threadNumber.__str__()
    gm_worker.set_client_id(hostID)
    for key in supportedModules.keys():
        logger.info('Registering: %s', key)
        gm_worker.register_task(key, executeCommand)

    failMaxSleep = 30
    failSleep = 1
    failSleepIncrementor = 2
    while True:
        try:
            gm_worker.work()
        except gearman.errors.ServerUnavailable as inst:
            logger.error('Gearman server is unavailable: %s. Retrying in %d seconds.', inst.args, failSleep)
            time.sleep(failSleep)
            if failSleep < failMaxSleep:
                failSleep += failSleepIncrementor


def startThreads(t=1):
    """Start a processing thread for each core (t=0), or a specified number of threads."""
    if t == 0:
        from externals.detectCores import detectCPUs
        t = detectCPUs()
    for i in range(t):
        t = threading.Thread(target=startThread, args=(i + 1, ))
        t.daemon = True
        t.start()


if __name__ == '__main__':
    try:
        loadSupportedModules(django_settings.CLIENT_MODULES_FILE)
        startThreads(django_settings.NUMBER_OF_TASKS)
        while True:
            time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        logger.info('Received keyboard interrupt, quitting threads.')
