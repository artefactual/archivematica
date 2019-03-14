#!/usr/bin/env python2

import logging
import os
import shutil

# storageService requires Django to be set up
import django

django.setup()
from django.db import transaction

# archivematicaCommon
import storageService as storage_service


class StorageServiceCreateFileError(Exception):
    pass


def _create_file(
    transfer_uuid, current_location, relative_transfer_path, backlog, backlog_path, size
):
    try:
        new_file = storage_service.create_file(
            uuid=transfer_uuid,
            origin_location=current_location["resource_uri"],
            origin_path=relative_transfer_path,
            current_location=backlog["resource_uri"],
            current_path=backlog_path,
            package_type="transfer",  # TODO use constant from storage service
            size=size,
        )
    except storage_service.Error as err:
        raise StorageServiceCreateFileError(err)
    if new_file is None:
        raise StorageServiceCreateFileError(
            "Value returned by Storage Service is unexpected"
        )
    if new_file.get("status") == "FAIL":
        raise StorageServiceCreateFileError(
            'Object returned by Storage Service has status "FAIL"'
        )
    return new_file


def main(job, transfer_uuid, transfer_path):
    current_location = storage_service.get_location(purpose="CP")[0]
    backlog = storage_service.get_location(purpose="BL")[0]

    # Get size recursively for Transfer
    size = 0
    for dirpath, _, filenames in os.walk(transfer_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            size += os.path.getsize(file_path)

    # Make Transfer path relative to Location
    shared_path = os.path.join(current_location["path"], "")
    relative_transfer_path = transfer_path.replace(shared_path, "")

    # TODO this should use the same value as
    # dashboard/src/components/filesystem_ajax/views.py DEFAULT_BACKLOG_PATH
    transfer_name = os.path.basename(transfer_path.rstrip("/"))
    backlog_path = os.path.join("originals", transfer_name)

    try:
        new_file = _create_file(
            transfer_uuid,
            current_location,
            relative_transfer_path,
            backlog,
            backlog_path,
            size,
        )
    except StorageServiceCreateFileError as err:
        errmsg = "Moving to backlog failed: {}.".format(err)
        logging.warning(errmsg)
        raise Exception(errmsg + " See logs for more details.")

    message = "Transfer moved to backlog: {}".format(new_file)
    logging.info(message)
    job.pyprint(message)

    # TODO update transfer location?  Files location?

    # Delete transfer from processing space
    shutil.rmtree(transfer_path)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transfer_uuid = job.args[1]
                transfer_path = job.args[2]
                job.set_status(main(job, transfer_uuid, transfer_path))
