#!/usr/bin/env python2

"""Archivematica Client (single-threaded Gearman Worker).

This executable does the following:

1. Loads tasks from config. Loads a list of performable tasks (client scripts)
   from a config file (typically that in lib/archivematicaClientModules) and
   creates a mapping from names of those tasks (e.g., 'normalize_v1.0') to the
   full paths of their corresponding (Python or bash) scripts (e.g.,
   '/src/MCPClient/lib/clientScripts/normalize.py').

2. Registers tasks with Gearman.  Create a Gearman worker and register the
   loaded tasks with the Gearman server, effectively saying "Hey, I can
   normalize files", etc.

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
import signal

import django
from django.conf import settings as django_settings
import gearman

from modules import load_supported_modules
from worker import get_worker


logger = logging.getLogger('archivematica.mcp.client')

# The worker object needs to be shared with the thread that runs the signal
# handler so it can stop it.
worker = None

# Dictionary of signals indexed by the signal ID. This is here so we can log the
# signal name instead of the ID when a signal is received.
SIGNALS = dict((getattr(signal, n), n)
               for n in dir(signal) if n.startswith('SIG') and '_' not in n)


def start_worker(gearman_servers):
    """Create worker and loop indifinitely to complete Gearman jobs."""
    global worker
    worker = get_worker(gearman_servers)

    try:
        logger.info('Ready to accept jobs.')
        worker.work()  # This is going to block.
    except gearman.errors.ServerUnavailable as err:
        logger.error('Gearman server is unavailable - %s', err)
    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutting down!')


def quit(signo, _frame):
    """SIGTERM and SIGINT signal handler.

    It closes the current connections with the Gearman server in order to
    interrupt the worker loop.
    """
    logger.info("Interrupted by signal %s, shutting down." % SIGNALS[signo])
    worker.shutdown()


def main():
    """Start single-threaded MCPClient."""
    # Set up quit signal handler.
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)

    django.setup()
    gearman_servers = django_settings.GEARMAN_SERVER.split(',')

    load_supported_modules(django_settings.CLIENT_MODULES_FILE)

    # This call blocks.
    start_worker(gearman_servers)


if __name__ == '__main__':
    main()
