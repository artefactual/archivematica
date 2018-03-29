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
from django.db import transaction
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

from django.conf import settings as mcpclient_settings

logger = get_script_logger('archivematica.mcp.client.elasticSearchIndexProcessTransfer')


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                if not mcpclient_settings.SEARCH_ENABLED:
                    logger.info('Skipping indexing: indexing is currently disabled.')
                    job.set_status(0)
                    continue

                transfer_path = job.args[1]
                transfer_uuid = job.args[2]
                try:
                    status = job.args[3]
                except IndexError:
                    status = ''

                elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
                client = elasticSearchFunctions.get_client()
                job.set_status(elasticSearchFunctions.index_files(client, 'transfers', 'transferfile', transfer_uuid, transfer_path, status=status, printfn=job.pyprint))
