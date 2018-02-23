#!/usr/bin/env python2

"""Archivematica Client (multi-threaded Gearman Worker).

This executable does the following:

1. Loads tasks from config. Loads a list of performable tasks (client scripts)
   from a config file (typically that in lib/archivematicaClientModules) and
   creates a mapping from names of those tasks (e.g., 'normalize_v1.0') to the
   full paths of their corresponding (Python or bash) scripts (e.g.,
   '/src/MCPClient/lib/clientScripts/normalize.py').

2. Registers tasks with Gearman. On multiple threads, create a Gearman worker
   and register the loaded tasks with the Gearman server, effectively saying
   "Hey, I can normalize files", etc.

When the MCPServer requests that the MCPClient perform a registered task, the
MCPClient thread calls ``execute_command``, passing it a job object which has a
``task`` attribute containing the name of the client script to run, and a
``data`` attribute whose value is a BLOB that unpickles to a dict containing
arguments to pass to the client script. The following then happens.

1. The client script is run in a subprocess with the provided arguments.

2. The exit code and output streams are pickled and returned.

"""

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

import logging
import threading
import time

import django
from django.conf import settings as django_settings
import gearman

from detect_cores import detect_cores
from modules import load_supported_modules
from worker import get_worker


logger = logging.getLogger('archivematica.mcp.client')


def start_worker(thread_number, gearman_servers):
    """Run a Gearman worker in this thread.

    The connection with the server will be retried indefinitely.
    """
    worker = get_worker(gearman_servers, name=thread_number)

def load_supported_modules(file):
    """Populate the global `supported_modules` dict by parsing the MCPClient
    modules config file (typically MCPClient/lib/archivematicaClientModules).
    """
    supported_modules_config = ConfigParser.RawConfigParser()
    supported_modules_config.read(file)
    for client_script, client_script_path in supported_modules_config.items(
            'supportedCommands'):
        load_supported_modules_support(client_script, client_script_path)
    if django_settings.LOAD_SUPPORTED_COMMANDS_SPECIAL:
        for client_script, client_script_path in supported_modules_config.items(
                'supportedCommandsSpecial'):
            load_supported_modules_support(client_script, client_script_path)


class ProcessGearmanJobError(Exception):
    pass


def _process_gearman_job(gearman_job, gearman_worker):
    """Process a gearman job/task: return a 3-tuple consisting of a script
    string (a command-line script with arguments), a task UUID string, and a
    boolean indicating whether output streams should be captured. Raise a
    custom exception if the client script is unregistered or if the task has
    already been started.
    """
    # ``client_script`` is a string matching one of the keys (i.e., client
    # scripts) in the global ``supported_modules`` dict.
    client_script = gearman_job.task
    task_uuid = str(gearman_job.unique)
    logger.info('Executing %s (%s)', client_script, task_uuid)
    data = cPickle.loads(gearman_job.data)
    utc_date = getUTCDate()
    arguments = data['arguments']
    if isinstance(arguments, unicode):
        arguments = arguments.encode('utf-8')
    client_id = gearman_worker.worker_client_id
    task = Task.objects.get(taskuuid=task_uuid)
    if task.starttime is not None:
        raise ProcessGearmanJobError({
            'exitCode': -1,
            'stdOut': '',
            'stdError': 'Detected this task has already started!\n'
                        'Unable to determine if it completed successfully.'})
    task.client = client_id
    task.starttime = utc_date
    task.save()
    client_script_full_path = supported_modules.get(client_script)
    if not client_script_full_path:
        raise ProcessGearmanJobError({
            'exitCode': -1,
            'stdOut': 'Error!',
            'stdError': 'Error! - Tried to run an unsupported command.'})
    replacement_dict['%date%'] = utc_date.isoformat()
    replacement_dict['%jobCreatedDate%'] = data['createdDate']
    # Replace replacement strings
    for var, val in replacement_dict.items():
        # TODO: this seems unneeded because the full path to the client
        # script can never contain '%date%' or '%jobCreatedDate%' and the
        # other possible vars have already been replaced.
        client_script_full_path = client_script_full_path.replace(var, val)
        arguments = arguments.replace(var, val)
    arguments = arguments.replace('%taskUUID%', task_uuid)
    script = client_script_full_path + ' ' + arguments
    return script, task_uuid


def _unexpected_error():
    logger.exception('Unexpected error')
    return cPickle.dumps({'exitCode': -1,
                          'stdOut': '',
                          'stdError': traceback.format_exc()})


@auto_close_db
def execute_command(gearman_worker, gearman_job):
    """Execute the command encoded in ``gearman_job`` and return its exit code,
    standard output and standard error as a pickled dict.
    """
    try:
        script, task_uuid = _process_gearman_job(
            gearman_job, gearman_worker)
    except ProcessGearmanJobError:
        return cPickle.dumps({
            'exitCode': 1,
            'stdOut': 'Archivematica Client Process Gearman Job Error!',
            'stdError': traceback.format_exc()})
    except Exception:
        return _unexpected_error()
    logger.info('<processingCommand>{%s}%s</processingCommand>',
                task_uuid, script)
    try:
        exit_code, std_out, std_error = executeOrRun(
            'command', script, stdIn='',
            printing=django_settings.CAPTURE_CLIENT_SCRIPT_OUTPUT,
            capture_output=django_settings.CAPTURE_CLIENT_SCRIPT_OUTPUT)
    except OSError:
        logger.exception('Execution failed')
        return cPickle.dumps({'exitCode': 1,
                              'stdOut': 'Archivematica Client Error!',
                              'stdError': traceback.format_exc()})
    except Exception:
        return _unexpected_error()
    return cPickle.dumps({'exitCode': exit_code,
                          'stdOut': std_out,
                          'stdError': std_error})


@auto_close_db
def start_thread(thread_number):
    """Setup a gearman client, for the thread."""
    gm_worker = gearman.GearmanWorker([django_settings.GEARMAN_SERVER])
    host_id = '{}_{}'.format(gethostname(), thread_number)
    gm_worker.set_client_id(host_id)
    for client_script in supported_modules:
        logger.info('Registering: %s', client_script)
        gm_worker.register_task(client_script, execute_command)
    fail_max_sleep = 30
    fail_sleep = 1
    fail_sleep_incrementor = 2
    while True:
        try:
            worker.work()
        except gearman.errors.ServerUnavailable as inst:
            logger.error('Gearman server is unavailable: %s. Retrying in %d'
                         ' seconds.', inst.args, fail_sleep)
            time.sleep(fail_sleep)
            if fail_sleep < fail_max_sleep:
                fail_sleep += fail_sleep_incrementor


def start_workers(gearman_servers, workers=1):
    """Start multiple threaded workers.

    The workers are executed as separate daemonic threads meaning that they are
    abruptly stopped at shutdown. Their resources may not be released properly.
    We should consider making them non-daemonic and use a suitable signalling
    mechanism such as ``threading.Event``.

    The number of workers created is determined by the ``workers`` argument.
    If ``0`` the function will create as many workers as CPU cores are detected
    in the operative system.
    """
    if workers == 0:
        workers = detect_cores()
    for index in range(workers):
        thread = threading.Thread(target=start_worker, args=(
            index + 1,
            gearman_servers))
        thread.daemon = True
        thread.start()


def main():
    """Start multi-threaded MCPClient."""
    django.setup()

    load_supported_modules(
        django_settings.CLIENT_MODULES_FILE,
        django_settings.LOAD_SUPPORTED_COMMANDS_SPECIAL)

    # This call does not block.
    start_workers(
        django_settings.GEARMAN_SERVER.split(','),
        django_settings.NUMBER_OF_TASKS)

    try:
        while True:
            time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        logger.info('Received keyboard interrupt, quitting threads.')


if __name__ == '__main__':
    main()
