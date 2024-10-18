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

import databaseFunctions
from django.db import transaction
from main.models import File


def recursivelyRemoveEmptyDirectories(job, dir):
    error_count = 0
    for root, dirs, _ in os.walk(dir, topdown=False):
        for directory in dirs:
            try:
                os.rmdir(os.path.join(root, directory))
            except OSError as e:
                job.pyprint(
                    f"{directory} could not be deleted: {e.args}",
                    file=sys.stderr,
                )
                error_count += 1
    return error_count


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                SIPDirectory = job.args[1]
                manual_normalization_dir = os.path.join(
                    SIPDirectory, "objects", "manualNormalization"
                )

                errorCount = 0

                if os.path.isdir(manual_normalization_dir):
                    # Delete normalization.csv if present
                    normalization_csv = os.path.join(
                        manual_normalization_dir, "normalization.csv"
                    )
                    if os.path.isfile(normalization_csv):
                        os.remove(normalization_csv)
                        # Need SIP UUID to get file UUID to remove file in DB
                        sipUUID = SIPDirectory[-37:-1]  # Account for trailing /

                        f = File.objects.get(
                            removedtime__isnull=True,
                            originallocation__endswith="normalization.csv",
                            sip_id=sipUUID,
                        )
                        databaseFunctions.fileWasRemoved(f.uuid)

                    # Recursively delete empty manual normalization dir
                    try:
                        errorCount += recursivelyRemoveEmptyDirectories(
                            job, manual_normalization_dir
                        )
                        os.rmdir(manual_normalization_dir)
                    except OSError as e:
                        job.pyprint(
                            f"{manual_normalization_dir} could not be deleted: {e.args}",
                            file=sys.stderr,
                        )
                        errorCount += 1

                job.set_status(errorCount)
