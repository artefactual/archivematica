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

import django
from django.db import transaction

django.setup()
# dashboard
from main.models import File

# archivematicaCommon
import fileOperations

# --sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%"
from optparse import OptionParser


def main(job):
    parser = OptionParser()
    parser.add_option("-s", "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option(
        "-d", "--sipDirectory", action="store", dest="sipDirectory", default=""
    )  # transferDirectory/
    parser.add_option(
        "-f", "--filePath", action="store", dest="filePath", default=""
    )  # transferUUID/sipUUID
    (opts, args) = parser.parse_args(job.args[1:])

    # Search for original file associated with the access file given in filePath
    filePathLike = opts.filePath.replace(
        os.path.join(opts.sipDirectory, "objects", "manualNormalization", "access"),
        "%SIPDirectory%objects",
        1,
    )
    i = filePathLike.rfind(".")
    if i != -1:
        # Matches "path/to/file/filename." Includes . so it doesn't false match foobar.txt when we wanted foo.txt
        filePathLike = filePathLike[: i + 1]
        # Matches the exact filename.  For files with no extension.
        filePathLike2 = filePathLike[:-1]

    unitIdentifierType = "sip_id"
    unitIdentifier = opts.sipUUID

    try:
        kwargs = {
            "removedtime__isnull": True,
            "filegrpuse": "original",
            unitIdentifierType: unitIdentifier,
        }
        try:
            f = File.objects.get(currentlocation__startswith=filePathLike, **kwargs)
        except (File.DoesNotExist, File.MultipleObjectsReturned):
            f = File.objects.get(currentlocation=filePathLike2, **kwargs)
    except (File.DoesNotExist, File.MultipleObjectsReturned) as e:
        # Original file was not found, or there is more than one original file with
        # the same filename (differing extensions)
        # Look for a CSV that will specify the mapping
        csv_path = os.path.join(
            opts.sipDirectory, "objects", "manualNormalization", "normalization.csv"
        )
        if os.path.isfile(csv_path):
            try:
                access_file = opts.filePath[
                    opts.filePath.index("manualNormalization/access/") :
                ]
            except ValueError:
                job.print_error(
                    "{0} not in manualNormalization directory".format(opts.filePath)
                )
                return 4
            original = fileOperations.findFileInNormalizationCSV(
                csv_path, "access", access_file, unitIdentifier, printfn=job.pyprint
            )
            if original is None:
                if isinstance(e, File.DoesNotExist):
                    job.print_error(
                        "No matching file for: {0}".format(
                            opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%")
                        )
                    )
                    return 3
                else:
                    job.print_error(
                        "Could not find {access_file} in {filename}".format(
                            access_file=access_file, filename=csv_path
                        )
                    )
                    return 2
            # If we found the original file, retrieve it from the DB
            kwargs = {
                "removedtime__isnull": True,
                "filegrpuse": "original",
                "originallocation__endswith": original,
                unitIdentifierType: unitIdentifier,
            }
            f = File.objects.get(**kwargs)
        else:
            if isinstance(e, File.DoesNotExist):
                job.print_error(
                    "No matching file for: ",
                    opts.filePath.replace(opts.SIPDirectory, "%SIPDirectory%", 1),
                )
                return 3
            elif isinstance(e, File.MultipleObjectsReturned):
                job.print_error(
                    "Too many possible files for: ",
                    opts.filePath.replace(opts.SIPDirectory, "%SIPDirectory%", 1),
                )
                return 2

    # We found the original file somewhere above, get the UUID and path
    originalFileUUID = f.uuid
    originalFilePath = f.originallocation

    job.print_output("matched: {%s}%s" % (originalFileUUID, originalFilePath))
    dstDir = os.path.join(opts.sipDirectory, "DIP", "objects")
    dstFile = originalFileUUID + "-" + os.path.basename(opts.filePath)

    # ensure unique output file name
    i = 0
    while os.path.exists(os.path.join(dstDir, dstFile)):
        i += 1
        dstFile = (
            originalFileUUID + "-" + str(i) + "-" + os.path.basename(opts.filePath)
        )

    try:
        if not os.path.isdir(dstDir):
            os.makedirs(dstDir)
    except:
        pass

    # Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
    # see http://docs.python.org/2/library/os.html
    os.rename(opts.filePath, os.path.join(dstDir, dstFile))

    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                try:
                    job.set_status(main(job))
                except fileOperations.FindFileInNormalizatonCSVError as e:
                    job.set_status(e.code)
