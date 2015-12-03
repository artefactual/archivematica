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

"""
This is the MCP Client.

It connects to the MCP server, and informs the server of the tasks it can
perform. The server can send a command (matching one of the tasks) for the
client to perform. The client will perform that task, and return the exit code
and output to the server.

For archivematica 0.9 release. Added integration with the transcoder.
The server will send the transcoder association pk, and file uuid to run.
The client is responsible for running the correct command on the file.
"""

import ConfigParser
import cPickle
import gearman
import logging
import os
import time
from socket import gethostname
import sys
import threading
import traceback

config = ConfigParser.SafeConfigParser()
config.read("/etc/archivematica/MCPClient/clientConfig.conf")

import django
django.setup()

from maindb.models import Task

from django_mysqlpool import auto_close_db
from custom_handlers import GroupWriteRotatingFileHandler
import databaseFunctions
from executeOrRunSubProcess import executeOrRun


printOutputLock = threading.Lock()
replacementDic = {
    "%sharedPath%": config.get('MCPClient', "sharedDirectoryMounted"),
    "%clientScriptsDirectory%": config.get('MCPClient', "clientScriptsDirectory")
}
supportedModules = {}


def loadSupportedModulesSupport(key, value):
    for key2, value2 in replacementDic.iteritems():
        value = value.replace(key2, value2)
    if not os.path.isfile(value):
        print >>sys.stderr, "Warning - Module can't find file, or relies on system path:{%s}%s" % (key.__str__(), value.__str__())
    supportedModules[key] = value + " "


def loadSupportedModules(file):
    supportedModulesConfig = ConfigParser.RawConfigParser()
    supportedModulesConfig.read(file)
    for key, value in supportedModulesConfig.items('supportedCommands'):
        loadSupportedModulesSupport(key, value)

    loadSupportedCommandsSpecial = config.get('MCPClient', "LoadSupportedCommandsSpecial")
    if loadSupportedCommandsSpecial.lower() == "yes" or \
    loadSupportedCommandsSpecial.lower() == "true":
        for key, value in supportedModulesConfig.items('supportedCommandsSpecial'):
            loadSupportedModulesSupport(key, value)


@auto_close_db
def executeCommand(gearman_worker, gearman_job):
    try:
        execute = gearman_job.task
        print "executing:", execute, "{", gearman_job.unique, "}"
        data = cPickle.loads(gearman_job.data)
        utcDate = databaseFunctions.getUTCDate()
        arguments = data["arguments"]#.encode("utf-8")
        if isinstance(arguments, unicode):
            arguments = arguments.encode("utf-8")

        sInput = ""
        clientID = gearman_worker.worker_client_id

        task = Task.objects.get(taskuuid=gearman_job.unique)
        if task.starttime is not None:
            exitCode = -1
            stdOut = ""
            stdError = """Detected this task has already started! Unable to determine if it completed successfully."""
            return cPickle.dumps({"exitCode" : exitCode, "stdOut": stdOut, "stdError": stdError})
        else:
            task.client = clientID
            task.starttime = utcDate
            task.save()

        if execute not in supportedModules:
            output = ["Error!", "Error! - Tried to run and unsupported command." ]
            exitCode = -1
            return cPickle.dumps({"exitCode" : exitCode, "stdOut": output[0], "stdError": output[1]})
        command = supportedModules[execute]

        replacementDic["%date%"] = utcDate.isoformat()
        replacementDic["%jobCreatedDate%"] = data["createdDate"]

        # Replace replacement strings
        for key in replacementDic.iterkeys():
            command = command.replace ( key, replacementDic[key] )
            arguments = arguments.replace ( key, replacementDic[key] )

        key = "%taskUUID%"
        value = gearman_job.unique.__str__()
        arguments = arguments.replace(key, value)

        # Execute command
        command += " " + arguments
        printOutputLock.acquire()
        print "<processingCommand>{" + gearman_job.unique + "}" + command.__str__() + "</processingCommand>"
        printOutputLock.release()
        exitCode, stdOut, stdError = executeOrRun("command", command, sInput, printing=False)
        return cPickle.dumps({"exitCode": exitCode, "stdOut": stdOut, "stdError": stdError})
    except OSError as ose:
        traceback.print_exc(file=sys.stdout)
        printOutputLock.acquire()
        print >>sys.stderr, "Execution failed:", ose
        printOutputLock.release()
        output = ["Archivematica Client Error!", traceback.format_exc()]
        exitCode = 1
        return cPickle.dumps({"exitCode": exitCode, "stdOut": output[0], "stdError": output[1]})
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        printOutputLock.acquire()
        print "Unexpected error:", e
        printOutputLock.release()
        output = ["", traceback.format_exc()]
        return cPickle.dumps({"exitCode": -1, "stdOut": output[0], "stdError": output[1]})


@auto_close_db
def startThread(threadNumber):
    """Setup a gearman client, for the thread."""
    gm_worker = gearman.GearmanWorker([config.get('MCPClient', "MCPArchivematicaServer")])
    hostID = gethostname() + "_" + threadNumber.__str__()
    gm_worker.set_client_id(hostID)
    for key in supportedModules.iterkeys():
        printOutputLock.acquire()
        print 'registering:"{}"'.format(key)
        printOutputLock.release()
        gm_worker.register_task(key, executeCommand)

    failMaxSleep = 30
    failSleep = 1
    failSleepIncrementor = 2
    while True:
        try:
            gm_worker.work()
        except gearman.errors.ServerUnavailable as inst:
            print >>sys.stderr, inst.args
            print >>sys.stderr, "Retrying in %d seconds." % (failSleep)
            time.sleep(failSleep)
            if failSleep < failMaxSleep:
                failSleep += failSleepIncrementor


@auto_close_db
def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)


def startThreads(t=1):
    """
    Start a processing thread for each core (t=0), or a specified number of
    threads.
    """
    t2 = threading.Thread(target=flushOutputs)
    t2.daemon = True
    t2.start()
    if t == 0:
        from externals.detectCores import detectCPUs
        t = detectCPUs()
    for i in range(t):
        t = threading.Thread(target=startThread, args=(i+1, ))
        t.daemon = True
        t.start()


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(levelname)-8s  %(asctime)s  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'logfile': {
            'level': 'INFO',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPClient/MCPClient.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 20 MiB
        },
        'verboselogfile': {
            'level': 'DEBUG',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPClient/MCPClient.debug.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 100 MiB
        },
    },
    'loggers': {
        'archivematica': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['logfile', 'verboselogfile'],
        'level': 'WARNING',
    }
}


if __name__ == '__main__':
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("archivematica.mcp.client")

    loadSupportedModules(config.get('MCPClient', "archivematicaClientModules"))
    startThreads(config.getint('MCPClient', "numberOfTasks"))
    tl = threading.Lock()
    tl.acquire()
    tl.acquire()
