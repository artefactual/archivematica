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
import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

from django.conf import settings as mcpclient_settings


logger = get_script_logger("archivematica.mcp.client.removeAIPFilesFromIndex")


if __name__ == '__main__':
    aip_uuid = sys.argv[1]

    if mcpclient_settings.DISABLE_SEARCH_INDEXING is True:
        logger.info('Skipping. Indexing is currently disabled.')

    elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
    client = elasticSearchFunctions.get_client()

    logger.info('Removing indexed files for AIP %s...', aip_uuid)
    elasticSearchFunctions.delete_aip_files(client, aip_uuid)
