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

from __future__ import print_function
import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

from config import settings


def index_transfer(transfer_path, transfer_uuid):
    # Check if Elasticsearch is enabled and exit otherwise
    indexing_enabled = settings.getboolean('MCPClient', 'elasticsearch_indexing_enabled', fallback=True)
    if not indexing_enabled:
        print('Skipping indexing because it is currently disabled.')
        return 0
    return elasticSearchFunctions.connect_and_index_files('transfers', 'transferfile', transfer_uuid, transfer_path)


if __name__ == '__main__':
    logger = get_script_logger('archivematica.mcp.client.elasticSearchIndexProcessTransfer')

    sys.exit(main(
        transfer_path=sys.argv[1],
        transfer_uuid=sys.argv[2]
    ))
