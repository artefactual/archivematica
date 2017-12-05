#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2011 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
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
# @author Mike Cantelon <mike@artefactual.com>

import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

from django.conf import settings as mcpclient_settings

logger = get_script_logger('archivematica.mcp.client.elasticSearchIndexProcessTransfer')


if __name__ == '__main__':
    if not mcpclient_settings.SEARCH_ENABLED:
        logger.info('Skipping indexing: indexing is currently disabled.')
        sys.exit(0)

    transfer_path = sys.argv[1]
    transfer_uuid = sys.argv[2]
    try:
        status = sys.argv[3]
    except IndexError:
        status = ''

    elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
    client = elasticSearchFunctions.get_client()
    sys.exit(elasticSearchFunctions.index_files(client, 'transfers', 'transferfile', transfer_uuid, transfer_path, status=status))
