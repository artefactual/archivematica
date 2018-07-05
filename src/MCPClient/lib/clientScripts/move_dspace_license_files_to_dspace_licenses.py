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
import lxml.etree as etree

# fileOperations requires Django to be set up
import django
django.setup()
from django.db import transaction
# archivematicaCommon
from fileOperations import updateFileLocation
from fileOperations import rename


def verifyMetsFileSecChecksums(job, metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory="./"):
    job.pyprint(metsFile)
    DspaceLicenses = "metadata/submissionDocumentation/DspaceLicenses"
    try:
        path = os.path.join(transferDirectory, DspaceLicenses)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        job.pyprint("error creating DspaceLicenses directory.")
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp"):
        # print etree.tostring(item)
        # print item

        USE = item.get("USE")
        if USE == "LICENSE":
            for item2 in item:
                if item2.tag == "{http://www.loc.gov/METS/}file":
                    for item3 in item2:
                        if item3.tag == "{http://www.loc.gov/METS/}FLocat":
                            fileLocation = item3.get("{http://www.w3.org/1999/xlink}href")
                            fileFullPath = os.path.join(relativeDirectory, fileLocation)
                            dest = os.path.join(transferDirectory, DspaceLicenses, os.path.basename(fileLocation))
                            rename(fileFullPath, dest)
                            rename_status = rename(fileFullPath, dest, printfn=job.pyprint, should_exit=False)
                            if rename_status:
                                return rename_status

                            src = fileFullPath.replace(transferDirectory, "%transferDirectory%")
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
