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
import os

import django

django.setup()
from django.db import transaction

# dashboard
from main.models import Transfer

# archivematicaCommon
from fileOperations import rename


def updateDB(dst, transferUUID):
    Transfer.objects.filter(uuid=transferUUID).update(currentlocation=dst)


def moveSIP(job, src, dst, transferUUID, sharedDirectoryPath):
    # os.rename(src, dst)
    if src.endswith("/"):
        src = src[:-1]

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))

    if os.path.isdir(src):
        dest += "/"
    updateDB(dest, transferUUID)

    return rename(src, dst, printfn=job.pyprint, should_exit=False)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                src = job.args[1]
                dst = job.args[2]
                transferUUID = job.args[3]
                sharedDirectoryPath = job.args[4]
                job.set_status(
                    moveSIP(job, src, dst, transferUUID, sharedDirectoryPath)
                )
