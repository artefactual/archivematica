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

import django

django.setup()
# dashboard
from main.models import Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from django.db import transaction

import metrics


logger = get_script_logger("archivematica.mcp.client.setTransferType")


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                transferUUID = job.args[1]
                transferType = job.args[2]

                Transfer.objects.filter(uuid=transferUUID, type__isnull=False).exclude(
                    type="Archivematica AIP"
                ).update(type=transferType)

    metrics.transfer_started(transferType)
