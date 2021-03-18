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

import django

django.setup()
from django.db import transaction

# dashboard
from main.models import SIP, Transfer

from change_names import change_path


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
                dst = change_path(SIPDirectory)
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
