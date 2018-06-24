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
import shutil
import os
import sys

import django
django.setup()
from django.db import transaction
# dashboard
from main.models import Transfer

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun


def extract(job, target, destinationDirectory):
    filename, file_extension = os.path.splitext(target)

    exitC = 0

    if file_extension != '.tgz' and file_extension != '.gz':
        job.pyprint('Unzipping...')

        command = """/usr/bin/7z x -bd -o"%s" "%s" """ % (destinationDirectory, target)
        exitC, stdOut, stdErr = executeOrRun("command", command, printing=False, capture_output=True)
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed extraction: ", command, "\r\n", stdErr, file=sys.stderr)
    else:
        job.pyprint('Untarring...')

        parent_dir = os.path.abspath(os.path.join(destinationDirectory, os.pardir))
        file_extension = ''
        command = ("tar zxvf " + target + ' --directory="%s"') % (parent_dir)
        exitC, stdOut, stdErr = executeOrRun("command", command, printing=False, capture_output=True)
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed to untar: ", command, "\r\n", stdErr, file=sys.stderr)

    return exitC


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                target = job.args[1]
                transferUUID = job.args[2]
                processingDirectory = job.args[3]
                sharedPath = job.args[4]

                basename = os.path.basename(target)
                basename = basename[:basename.rfind(".")]

                destinationDirectory = os.path.join(processingDirectory, basename)

                # trim off '.tar' if present (os.path.basename doesn't deal well with '.tar.gz')
                try:
                    tar_extension_position = destinationDirectory.rindex('.tar')
                    destinationDirectory = destinationDirectory[:tar_extension_position]
                except ValueError:
                    pass

                zipLocation = os.path.join(processingDirectory, os.path.basename(target))

                # move to processing directory
                shutil.move(target, zipLocation)

                # extract
                exit_code = extract(job, zipLocation, destinationDirectory)

                if exit_code != 0:
                    job.set_status(exit_code)
                    continue

                # checkForTopLevelBag
                listdir = os.listdir(destinationDirectory)
                if len(listdir) == 1:
                    internalBagName = listdir[0]
                    # print "ignoring BagIt internal name: ", internalBagName
                    temp = destinationDirectory + "-tmp"
                    shutil.move(destinationDirectory, temp)
                    # destinationDirectory = os.path.join(processingDirectory, internalBagName)
                    shutil.move(os.path.join(temp, internalBagName), destinationDirectory)
                    os.rmdir(temp)

                # update transfer
                destinationDirectoryDB = destinationDirectory.replace(sharedPath, "%sharedPath%", 1)
                Transfer.objects.filter(uuid=transferUUID).update(currentlocation=destinationDirectoryDB)

                # remove bag
                os.remove(zipLocation)
