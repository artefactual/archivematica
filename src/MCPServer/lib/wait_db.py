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

import logging
import time

import django


"""
Using the default logging module-level functions intentionally as the custom
application logger 'archivematica.mcp.server' is not available at this time.
"""


def wait_db():
    """
    Simple retry pattern when django.db.connection.cursor() raises an
    OperationalError exception. In MySQL, this frequently happens when there
    are too many connections, the host name coult not be resolved,
    communication errors, etc...
    """
    attempt = 1
    fail_sleep = 1
    fail_sleep_inc = 2
    fail_max_sleep = 30
    while True:
        try:
            cursor = django.db.connection.cursor()
        except django.db.utils.OperationalError:
            if fail_sleep < fail_max_sleep:
                fail_sleep += fail_sleep_inc
            logging.error('Connection attempt to MySQL failed (attempt %d). Trying again in %d seconds...', attempt, fail_sleep)
            attempt += 1
            time.sleep(fail_sleep)
        else:
            logging.info('The connection to the database succeeded.')
            cursor.close()
            return
