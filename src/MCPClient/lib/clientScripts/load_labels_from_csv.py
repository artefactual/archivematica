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

import csv
import os

import django

django.setup()
from django.db import transaction

# dashboard
from main.models import File


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transferUUID = job.args[1]
                fileLabels = job.args[2]
                labelFirst = False

                if not os.path.isfile(fileLabels):
                    job.pyprint("No such file:", fileLabels)
                    job.set_status(0)
                    continue

                # use universal newline mode to support unusual newlines, like \r
                with open(fileLabels, "rbU") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if labelFirst:
                            label = row[0]
                            filePath = row[1]
                        else:
                            label = row[1]
                            filePath = row[0]
                        filePath = os.path.join("%transferDirectory%objects/", filePath)
                        File.objects.filter(
                            originallocation=filePath, transfer_id=transferUUID
                        ).update(label=label)
