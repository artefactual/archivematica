#!/usr/bin/env python2

import argparse
import os

import django

django.setup()
from django.db import transaction

# archivematicaCommon
import storageService as storage_service

from main.models import File, Transfer

import metrics


REJECTED = "reject"
FAILED = "fail"


def main(job, fail_type, transfer_uuid, transfer_path):
    # Update storage service that reingest failed
    session = storage_service._storage_api_session()
    aip_uuid = None
    # Get aip_uuid from reingest METS name
    if os.path.isdir(os.path.join(transfer_path, "data")):
        mets_dir = os.path.join(transfer_path, "data")
    elif os.path.isdir(os.path.join(transfer_path, "metadata")):
        mets_dir = os.path.join(transfer_path, "metadata")
    else:
        mets_dir = transfer_path
    for item in os.listdir(mets_dir):
        if item.startswith("METS"):
            aip_uuid = item.replace("METS.", "").replace(".xml", "")

    job.pyprint("AIP UUID for this Transfer is", aip_uuid)
    if aip_uuid:
        url = storage_service._storage_service_url() + "file/" + aip_uuid + "/"
        try:
            session.patch(url, json={"reingest": None})
        except Exception:
            # Ignore errors, as this may not be reingest
            pass

    # Delete files for reingest transfer
    # A new reingest doesn't know to delete this because the UUID is different from the AIP, and it causes problems when re-parsing these files
    transfer = Transfer.objects.get(uuid=transfer_uuid)
    if transfer.type == "Archivematica AIP":
        File.objects.filter(transfer_id=transfer_uuid).delete()

    metrics.transfer_failed(transfer.type, fail_type)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser(
        description="Cleanup from failed/rejected Transfers."
    )
    parser.add_argument("fail_type", help='"%s" or "%s"' % (REJECTED, FAILED))
    parser.add_argument("transfer_uuid", help="%SIPUUID%")
    parser.add_argument("transfer_path", help="%SIPDirectory%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(
                    main(job, args.fail_type, args.transfer_uuid, args.transfer_path)
                )
