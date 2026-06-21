#!/usr/bin/env python
"""Clean database and Storage Service state for failed transfers.

Most callers reach this script after a transfer has been materialized in an
Archivematica workflow directory, so the script can inspect the transfer path
for reingest METS cleanup. API-created transfers can fail earlier while the
transfer-source retrieval task is still copying from Storage Service. In that
case there may be no transfer directory to inspect, but the workflow still needs
to record the transfer failure and finish cleanup without replacing the
retrieval error with a cleanup error. ``--allow-missing-path`` is limited to
that pre-materialization failure path; the default remains strict for existing
failed-transfer cleanup links.
"""

import argparse
import os
from collections.abc import Sequence

import django

django.setup()

from django.db import transaction

import archivematica.archivematicaCommon.storageService as storage_service
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client import metrics
from archivematica.MCPClient.client.job import Job

REJECTED = "reject"
FAILED = "fail"


def main(
    job: Job,
    fail_type: str,
    transfer_uuid: str,
    transfer_path: str,
    allow_missing_path: bool = False,
) -> int:
    """Clean one transfer, optionally tolerating pre-materialization failures."""
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
    if allow_missing_path and not os.path.isdir(mets_dir):
        # Retrieval can fail before there is a directory for legacy cleanup to scan.
        job.pyprint(
            "Transfer path does not exist or is not a directory; "
            "skipping reingest cleanup:",
            transfer_path,
        )
    else:
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


def call(jobs: Sequence[Job]) -> None:
    """Parse workflow arguments and clean each failed or rejected transfer."""
    parser = argparse.ArgumentParser(
        description="Cleanup from failed/rejected Transfers."
    )
    parser.add_argument("fail_type", help=f'"{REJECTED}" or "{FAILED}"')
    parser.add_argument("transfer_uuid", help="%%SIPUUID%%")
    parser.add_argument("transfer_path", help="%%SIPDirectory%%")
    parser.add_argument("--allow-missing-path", action="store_true")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(
                    main(
                        job,
                        args.fail_type,
                        args.transfer_uuid,
                        args.transfer_path,
                        allow_missing_path=args.allow_missing_path,
                    )
                )
