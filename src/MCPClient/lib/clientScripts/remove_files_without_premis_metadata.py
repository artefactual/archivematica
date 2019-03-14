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

import argparse
import os

import django

django.setup()
from main.models import File


def verifyFileUUID(job, fileUUID, filePath, sipDirectory):
    if fileUUID == "None":
        relativeFilePath = filePath.replace(sipDirectory, "%SIPDirectory%", 1)
        job.print_output(
            "Deleting", relativeFilePath, "because it is not in the database."
        )
        os.remove(filePath)
        return
    file_ = File.objects.get(uuid=fileUUID)
    if file_.filegrpuse == "deleted":
        if os.path.exists(filePath):
            relativeFilePath = filePath.replace(sipDirectory, "%SIPDirectory%", 1)
            job.print_output(
                "Deleting", relativeFilePath, "because it is marked as deleted"
            )
            os.remove(filePath)


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--inputFile", default="")
    parser.add_argument("-o", "--sipDirectory", default="")
    parser.add_argument("-i", "--fileUUID", default="None")

    for job in jobs:
        with job.JobContext():
            args = parser.parse_args(job.args[1:])

            verifyFileUUID(job, args.fileUUID, args.inputFile, args.sipDirectory)
