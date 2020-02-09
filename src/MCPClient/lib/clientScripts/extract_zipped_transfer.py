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
from fileOperations import get_extract_dir_name


def extract(job, target, destinationDirectory):
    filename, file_extension = os.path.splitext(target)

    exitC = 0

    if file_extension != ".tgz" and file_extension != ".gz":
        job.pyprint("Unzipping...")

        command = """/usr/bin/7z x -bd -o"%s" "%s" """ % (destinationDirectory, target)
        exitC, stdOut, stdErr = executeOrRun(
            "command", command, printing=False, capture_output=True
        )
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed extraction: ", command, "\r\n", stdErr, file=sys.stderr)
    else:
        job.pyprint("Untarring...")

        parent_dir = os.path.abspath(os.path.join(destinationDirectory, os.pardir))
        file_extension = ""
        command = ("tar zxvf " + target + ' --directory="%s"') % (parent_dir)
        exitC, stdOut, stdErr = executeOrRun(
            "command", command, printing=False, capture_output=True
        )
        if exitC != 0:
            job.pyprint(stdOut)
            job.pyprint("Failed to untar: ", command, "\r\n", stdErr, file=sys.stderr)

    return exitC


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sip_directory", type=str)
    parser.add_argument("sip_uuid", type=str)
    parser.add_argument("processing_directory", type=str)
    parser.add_argument("shared_path", type=str)
    parser.add_argument("--bag", action="store_true")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                target = args.sip_directory
                transferUUID = args.sip_uuid
                processingDirectory = args.processing_directory
                sharedPath = args.shared_path
                isBag = args.bag

                basename = os.path.basename(target)
                destinationDirectory = os.path.join(processingDirectory, basename)

                destinationDirectory = get_extract_dir_name(destinationDirectory)

                zipLocation = os.path.join(
                    processingDirectory, os.path.basename(target)
                )

                # move to processing directory
                shutil.move(target, zipLocation)

                # extract
                exit_code = extract(job, zipLocation, destinationDirectory)

                if exit_code != 0:
                    job.set_status(exit_code)
                    continue

                # Ensure that the only thing in the destination dir is the
                # top level directory from the extracted file, with the
                # exception of certain files that may have been copied here
                # previously. (For now this is just the processing config.)
                # These files will need to be moved down a level.
                if isBag:
                    preexisting_files = {"processingMCP.xml"}
                    listdir = set(os.listdir(destinationDirectory))
                    to_move = listdir & preexisting_files
                    listdir -= preexisting_files

                    if len(listdir) == 1:
                        internalBagName = listdir.pop()

                        for filename in to_move:
                            shutil.move(
                                os.path.join(destinationDirectory, filename),
                                os.path.join(destinationDirectory, internalBagName),
                            )

                        # print "ignoring BagIt internal name: ", internalBagName
                        temp = destinationDirectory + "-tmp"
                        shutil.move(destinationDirectory, temp)
                        shutil.move(
                            os.path.join(temp, internalBagName), destinationDirectory
                        )
                        os.rmdir(temp)

                # update transfer
                destinationDirectoryDB = destinationDirectory.replace(
                    sharedPath, "%sharedPath%", 1
                )
                Transfer.objects.filter(uuid=transferUUID).update(
                    currentlocation=destinationDirectoryDB
                )

                # remove zipfile
                os.remove(zipLocation)
