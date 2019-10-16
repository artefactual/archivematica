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
from optparse import OptionParser
import re

import django
import scandir
from django.db import transaction

django.setup()
# dashboard
from main.models import File


def something(job, SIPDirectory, serviceDirectory, objectsDirectory, SIPUUID, date):
    # exitCode = 435
    exitCode = 0
    job.pyprint(SIPDirectory)
    # For every file, & directory Try to find the matching file & directory in the objects directory
    for (path, dirs, files) in scandir.walk(serviceDirectory):
        for file in files:
            servicePreExtension = "_me"
            originalPreExtension = "_m"
            file1Full = os.path.join(path, file).replace(
                SIPDirectory, "%SIPDirectory%", 1
            )  # service

            a = file.rfind(servicePreExtension + ".")
            if a != -1:
                file2Full = os.path.join(
                    path, file[:a] + originalPreExtension + "."
                ).replace(
                    SIPDirectory + "objects/service/", "%SIPDirectory%objects/", 1
                )  # service
            else:
                a = file.rfind(".")
                if a != -1:  # if a period is found
                    a += 1  # include the period
                file2Full = os.path.join(path, file[:a]).replace(
                    SIPDirectory + "objects/service/", "%SIPDirectory%objects/", 1
                )  # service

            f = File.objects.get(
                currentlocation=file1Full, removedtime__isnull=True, sip_id=SIPUUID
            )
            f.filegrpuse = "service"

            grp_file = File.objects.get(
                currentlocation__startswith=file2Full,
                removedtime__isnull=True,
                sip_id=SIPUUID,
            )
            f.filegrpuuid = grp_file.uuid
            f.save()

    return exitCode


# only works if files have the same extension
def regular(SIPDirectory, objectsDirectory, SIPUUID, date):
    searchForRegularExpressions = True
    if not searchForRegularExpressions:
        return

    for (path, dirs, files) in scandir.walk(objectsDirectory):
        for file in files:
            m = re.search("_me\.[a-zA-Z0-9]{2,4}$", file)
            if m is not None:
                file1Full = os.path.join(path, file).replace(
                    SIPDirectory, "%SIPDirectory%", 1
                )  # service
                file2 = file.replace(m.group(0), m.group(0).replace("_me", "_m", 1))
                file2Full = os.path.join(path, file2).replace(
                    SIPDirectory, "%SIPDirectory%", 1
                )  # original

                f = File.objects.get(
                    currentlocation=file1Full, removedtime__isnull=True, sip_id=SIPUUID
                )
                f.filegrpuse = "service"

                grp_file = File.objects.get(
                    currentlocation__startswith=file2Full,
                    removedtime__isnull=True,
                    sip_id=SIPUUID,
                )
                f.filegrpuuid = grp_file.uuid
                f.save()


def call(jobs):
    parser = OptionParser()
    # '--SIPDirectory "%SIPDirectory%" --serviceDirectory "objects/service/" --objectsDirectory "objects/" --SIPUUID "%SIPUUID%" --date "%date%"' );
    parser.add_option(
        "-s", "--SIPDirectory", action="store", dest="SIPDirectory", default=""
    )
    parser.add_option("-u", "--SIPUUID", action="store", dest="SIPUUID", default="")
    parser.add_option(
        "-a", "--serviceDirectory", action="store", dest="serviceDirectory", default=""
    )
    parser.add_option(
        "-o", "--objectsDirectory", action="store", dest="objectsDirectory", default=""
    )
    parser.add_option("-t", "--date", action="store", dest="date", default="")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                (opts, args) = parser.parse_args(job.args[1:])

                SIPDirectory = opts.SIPDirectory
                serviceDirectory = os.path.join(SIPDirectory, opts.serviceDirectory)
                objectsDirectory = os.path.join(SIPDirectory, opts.objectsDirectory)
                SIPUUID = opts.SIPUUID
                date = opts.date

                if not os.path.isdir(serviceDirectory):
                    job.pyprint("no service directory in this sip")
                    # regular(SIPDirectory, objectsDirectory, SIPUUID, date)
                    job.set_status(0)
                    continue

                exitCode = something(
                    job, SIPDirectory, serviceDirectory, objectsDirectory, SIPUUID, date
                )
                job.set_status(exitCode)
