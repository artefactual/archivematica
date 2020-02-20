#!/usr/bin/env python

import os
import sys

import django

django.setup()
from django.db import transaction

# dashboard
from main.models import Transfer


def main(job, transfer_path, transfer_uuid, shared_path):
    """Move a Transfer that is a file into a directory.

    Given a transfer that is one file, move the file into a directory
    with the same basename and update the DB for the new path.  No
    action taken if the transfer is already a directory.

    WARNING This should not be run inside a watched directory - may
    result in duplicated transfers.

    :param transfer_path: Path to the current transfer, file or folder
    :param transfer_uuid: UUID of the transfer to update
    :param shared_path: Value of the %sharedPath% variable
    """
    # If directory, return unchanged
    if os.path.isdir(transfer_path):
        job.pyprint(transfer_path, "is a folder, no action needed. Exiting.")
        return 0
    # If file, move into directory and update transfer
    dirpath = os.path.splitext(transfer_path)[0]
    basename = os.path.basename(transfer_path)
    if os.path.exists(dirpath):
        job.pyprint(
            "Cannot move file",
            transfer_path,
            "to folder",
            dirpath,
            "because it already exists",
            file=sys.stderr,
        )
        return 1
    os.mkdir(dirpath)
    new_path = os.path.join(dirpath, basename)
    job.pyprint("Moving", transfer_path, "to", new_path)
    os.rename(transfer_path, new_path)

    db_path = os.path.join(dirpath.replace(shared_path, "%sharedPath%", 1), "")
    job.pyprint("Updating transfer", transfer_uuid, "path to", db_path)
    Transfer.objects.filter(uuid=transfer_uuid).update(currentlocation=db_path)
    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transfer_path = job.args[1]
                transfer_uuid = job.args[2]
                shared_path = job.args[3]
                job.set_status(main(job, transfer_path, transfer_uuid, shared_path))
