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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import print_function

import sys
import uuid

import django
django.setup()
# dashboard
from main.models import Event

# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoEvents

from django.conf import settings as mcpclient_settings
from clamd import ClamdUnixSocket, ClamdNetworkSocket, ClamdError


logger = get_script_logger("archivematica.mcp.client.clamscan")

DEFAULT_TIMEOUT = 10


def get_client(addr):
    if ':' in addr:
        host, port = addr.split(':')
        return ClamdNetworkSocket(host=host, port=int(port), timeout=DEFAULT_TIMEOUT)
    return ClamdUnixSocket(path=addr)


def record_event(fileUUID, version, date, outcome):
    if not fileUUID or fileUUID == 'None':
        return
    logger.info('Recording event for fileUUID=%s outcome=%s', fileUUID, outcome)
    program = 'Clam AV'
    version, virus_defs, virus_defs_date = version.split('/')
    event_detail = 'program="{}"; version="{}"; virusDefinitions="{}/{}"' \
        .format(
            program,
            version,
            virus_defs,
            virus_defs_date
        )
    return insertIntoEvents(
        fileUUID=fileUUID,
        eventIdentifierUUID=str(uuid.uuid4()),
        eventType="virus check",
        eventDateTime=date,
        eventDetail=event_detail,
        eventOutcome=outcome)


def main(fileUUID, target, date):
    # Check if scan event already exists for this file - if so abort early
    count = Event.objects.filter(file_uuid_id=fileUUID, event_type='virus check').count()
    if count >= 1:
        logger.info('Virus scan already performed, not running scan again')
        return 0

    try:
        client = get_client(mcpclient_settings.CLAMAV_SERVER)
        version = client.version()
    except ClamdError:
        logger.error('Clamd error', exc_info=True)
        return 1

    try:
        result = client.scan(target)
    except ClamdError:
        logger.error('Clamd error', exc_info=True)
        record_event(fileUUID, version, date, outcome='Fail')
        return 1

    try:
        state, details = result[target]
    except KeyError:
        logger.error('File not scanned: %s', target)
        return 1
    if state == 'OK':
        record_event(fileUUID, version, date, outcome='Pass')
    else:
        record_event(fileUUID, version, date, outcome='Fail')
        logger.info('Clamd state=%s - %s', state, details)
        return 1


if __name__ == '__main__':
    fileUUID = sys.argv[1]
    target = sys.argv[2]
    date = sys.argv[3]

    sys.exit(main(fileUUID, target, date))
