#!/usr/bin/env python2

import argparse

import django
from django.db import transaction

django.setup()
# dashboard
from main import models

# archivematicaCommon
import storageService as storage_service

import metrics


REJECTED = "reject"
FAILED = "fail"


def main(job, fail_type, sip_uuid):
    # Update SIP Arrange table for failed SIP
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list("uuid", flat=True)
    job.pyprint("Allow files in this SIP to be arranged. UUIDs:", file_uuids)
    models.SIPArrange.objects.filter(sip_id=sip_uuid).delete()

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
    parser.add_argument("fail_type", help='"%s" or "%s"' % (REJECTED, FAILED))
    parser.add_argument("sip_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(main(job, args.fail_type, args.sip_uuid))

    metrics.sip_failed(args.fail_type)
