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
