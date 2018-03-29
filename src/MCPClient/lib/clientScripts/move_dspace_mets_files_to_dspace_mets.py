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

# fileOperations requires Django to be set up
import django
django.setup()
from django.db import transaction
# archivematicaCommon
from fileOperations import updateFileLocation
from fileOperations import rename


def verifyMetsFileSecChecksums(job, metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory="./"):
    job.pyprint(metsFile)
    DSpaceMets = "metadata/submissionDocumentation/DSpaceMets"
    try:
        path = os.path.join(transferDirectory, DSpaceMets)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        job.pyprint("error creating DSpaceMets directory.")
    exitCode = 0

    metsDirectory = os.path.basename(os.path.dirname(metsFile))

    if metsDirectory == "DSpace_export":
        outputDirectory = path
    else:
        outputDirectory = os.path.join(path, metsDirectory)
        if not os.path.isdir(outputDirectory):
            os.mkdir(outputDirectory)

    dest = os.path.join(outputDirectory, "mets.xml")
    rename_status = rename(metsFile, dest, printfn=job.pyprint, should_exit=False)
    if rename_status:
        return rename_status

    src = metsFile.replace(transferDirectory, "%transferDirectory%")
    dst = dest.replace(transferDirectory, "%transferDirectory%")
    eventDetail = ""
    eventOutcomeDetailNote = "moved from=\"" + src + "\"; moved to=\"" + dst + "\""
    updateFileLocation(src, dst, "movement", date, eventDetail, transferUUID=transferUUID, eventOutcomeDetailNote=eventOutcomeDetailNote)

    return exitCode


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                metsFile = job.args[1]
                date = job.args[2]
                taskUUID = job.args[3]
                transferDirectory = job.args[4]
                transferUUID = job.args[5]

                ret = verifyMetsFileSecChecksums(job, metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
                job.set_status(ret)
