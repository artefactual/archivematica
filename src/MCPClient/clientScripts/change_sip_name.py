#!/usr/bin/env python
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
import os
import sys

import django

django.setup()
from change_names import change_path
from django.db import transaction
from main.models import SIP
from main.models import Transfer


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                # job.args[3] (date) is unused.
                SIPDirectory = job.args[1]
                sipUUID = job.args[2]
                sharedDirectoryPath = job.args[4]
                unitType = job.args[5]

                # Remove trailing slash
                if SIPDirectory[-1] == "/":
                    SIPDirectory = SIPDirectory[:-1]

                if unitType == "SIP":
                    klass = SIP
                    locationColumn = "currentpath"
                elif unitType == "Transfer":
                    klass = Transfer
                    locationColumn = "currentlocation"
                else:
                    job.pyprint("invalid unit type: ", unitType, file=sys.stderr)
                    job.set_status(1)
                    continue
                max_filename = os.pathconf(SIPDirectory, "PC_NAME_MAX")
                dst = change_path(SIPDirectory, max_filename)
                if SIPDirectory != dst:
                    dst = dst.replace(sharedDirectoryPath, "%sharedPath%", 1) + "/"
                    job.pyprint(
                        SIPDirectory.replace(sharedDirectoryPath, "%sharedPath%", 1)
                        + " -> "
                        + dst
                    )

                    unit = klass.objects.get(uuid=sipUUID)
                    setattr(unit, locationColumn, dst)
                    unit.save()
