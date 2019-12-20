#!/usr/bin/env python2
"""Attempts to remove a file if its name matches a list of filenames that
should be removed. If it does, and if the removal was successful, then it
updates the ``File`` model of the file accordingly and also creates a "file
removed" event in the database. Command line required arguments are the path to
the file and its UUID. There is a default list of file names that are deleted;
however, this can be overridden in MCPClient/clientConfig.conf s
"""

import os
import shutil

# databaseFunctions requires Django to be set up
import django
from django.db import transaction

django.setup()
# archivematicaCommon
from databaseFunctions import fileWasRemoved

from django.conf import settings as mcpclient_settings


def remove_file(job, target_file, file_uuid):
    removableFiles = [e.strip() for e in mcpclient_settings.REMOVABLE_FILES.split(",")]
    basename = os.path.basename(target_file)
    if basename in removableFiles:
        job.print_output(
            "Removing {filename} (UUID: {uuid})".format(
                uuid=file_uuid, filename=basename
            )
        )
        try:
            os.remove(target_file)
        except OSError:
            shutil.rmtree(target_file)
        # Gearman passes parameters as strings, so None (NoneType) becomes
        # "None" (string)
        if file_uuid and file_uuid != "None":
            fileWasRemoved(file_uuid)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                target = job.args[1]
                file_uuid = job.args[2]

                job.set_status(remove_file(job, target, file_uuid))
