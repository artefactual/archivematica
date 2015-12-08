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

#~DOC~
#
# --- This is the MCP Client---
#It connects to the MCP server, and informs the server of the tasks it can perform.
#The server can send a command (matching one of the tasks) for the client to perform.
#The client will perform that task, and return the exit code and output to the server.
#
#For archivematica 0.9 release. Added integration with the transcoder.
#The server will send the transcoder association pk, and file uuid to run.
#The client is responsible for running the correct command on the file.

import cPickle
import logging
import os
import socket
import time
import sys
import threading
import traceback

import gearman

import django
django.setup()
from main.models import Task

from django_mysqlpool import auto_close_db
from custom_handlers import GroupWriteRotatingFileHandler
from externals.detectCores import detectCPUs
import databaseFunctions
from executeOrRunSubProcess import executeOrRun

from .config import LOGGING_CONFIG, settings
from .modules import replacement_dict, supported_modules

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('archivematica.mcp.client')


@auto_close_db
def execute_task(gearman_worker, gearman_job):
    """
    This is the function callback that processes the tasks assigned to this
    worker. It should return a serialized dict (using cPickle) with the
    following three fields: `exitCode`, `stdOut` and `stdError`.
    """
    try:
        execute = gearman_job.task
        worker_id = gearman_worker.worker_client_id
        date = databaseFunctions.getUTCDate()
        data = cPickle.loads(gearman_job.data)

        logger.info('Executing %s (%s)', execute, gearman_job.unique)

        # Extract arguments and ensure that they are encoded in utf-8
        arguments = data['arguments']
        if isinstance(arguments, unicode):
            arguments = arguments.encode('utf-8')

        task = Task.objects.get(taskuuid=gearman_job.unique)
        if task.starttime is not None:
            return cPickle.dumps({
                'exitCode': -1,
                'stdOut': '',
                'stdError': 'Detected this task has already started! Unable to determine if it completed successfully.'
            })

        # Update task
        task.client = worker_id
        task.starttime = date
        task.save()

        # Exit if the module is not supported by this client
        if execute not in supported_modules:
            return cPickle.dumps({
                'exitCode': -1,
                'stdOut': 'Error!',
                'stdError': 'Error! - Tried to run and unsupported command.'
            })

        command = supported_modules[execute]

        # Replace replacement strings
        repdict = replacement_dict.copy()
        repdict['%date%'] = date.isoformat()
        repdict['%jobCreatedDate%'] = data['createdDate']
        for key in repdict.iterkeys():
            command = command.replace(key, repdict[key])
            arguments = arguments.replace(key, repdict[key])
        key = '%taskUUID%'
        value = gearman_job.unique.__str__()
        arguments = arguments.replace(key, value)
        command += '{} '.format(arguments)

        # Execute command
        logger.info('<processingCommand>{%s}%s</processingCommand>', gearman_job.unique, command)
        exitCode, stdOut, stdError = executeOrRun("command", command, stdIn='', printing=False)
        return cPickle.dumps({
            'exitCode': exitCode,
            'stdOut': stdOut,
            'stdError': stdError
        })

    except OSError as ose:
        logger.exception('Gearman task failed')
        return cPickle.dumps({
            'exitCode': 1,
            'stdOut': 'Archivematica Client Error!',
            'stdError': traceback.format_exc()
        })

    except Exception as e:
        logger.exception('Gearman task failed (unexpected error)')
        return cPickle.dumps({
            'exitCode': -1,
            'stdOut': '',
            'stdError': traceback.format_exc()
        })


@auto_close_db
def start_worker(worker_id):
    """
    Start a Gearman worker loop. If the Gearman server is unavailable this
    function will retry more connection attempts with a delay between attempts
    that starts with 1 second and increments 2 seconds each time. The function
    gives up when the delay reaches 30 seconds.
    """
    worker = gearman.GearmanWorker([settings.get('MCPClient', 'server')])

    host_id = '{}_{}'.format(socket.gethostname(), worker_id)
    worker.set_client_id(host_id)

    for key in supported_modules.iterkeys():
        logger.info('Registering function %s', key)
        worker.register_task(key, execute_task)

    fail_sleep = 1
    fail_sleep_inc = 2
    fail_max_sleep = 30
    while True:
        try:
            # Loop indefinitely, complete tasks from all connections.
            worker.work()
        except gearman.errors.ServerUnavailable as inst:
            logger.error('Gearman server is unavailable: %s. Retrying in %s seconds.', inst.args, fail_sleep)
            time.sleep(fail_sleep)
            if fail_sleep < fail_max_sleep:
                fail_sleep += fail_sleep_inc


def start_workers():
    """
    Start daemonic threaded Gearman workers.
    """
    workers = 1
    try:
        workers = settings.getint('MCPClient', 'workers')
    except:
        pass
    if workers == 0:
        workers = detectCPUs()
    for i in range(workers):
        t = threading.Thread(target=start_worker, args=(i+1,))
        t.daemon = True
        t.start()


if __name__ == '__main__':
    try:
        start_workers()
        while True:
            time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        # TODO: clean up worker threads!
        logger.info('Received keyboard interrupt, quitting threads.')
