#!/usr/bin/env python
import argparse

import django
from django.db import transaction

django.setup()

import archivematica.archivematicaCommon.storageService as storage_service
from archivematica.MCPClient.client import metrics

REJECTED = "reject"
FAILED = "fail"


def main(job, fail_type, sip_uuid):
    # Update storage service that reingest failed
    session = storage_service._storage_api_session()
    url = storage_service._storage_service_url() + "file/" + sip_uuid + "/"
    try:
        session.patch(url, json={"reingest": None})
    except Exception:
        # Ignore errors, as this may not be reingest
        pass
    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="Cleanup from failed/rejected SIPs.")
    parser.add_argument("fail_type", help=f'"{REJECTED}" or "{FAILED}"')
    parser.add_argument("sip_uuid", help="%%SIPUUID%%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(main(job, args.fail_type, args.sip_uuid))

    metrics.sip_failed(args.fail_type)
