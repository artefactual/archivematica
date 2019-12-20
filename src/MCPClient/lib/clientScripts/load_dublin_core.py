#!/usr/bin/env python2

import json
import os
import sys

import django

django.setup()
from django.db import transaction

# dashboard
from main import models

# This is the UUID of SIP from the `MetadataAppliesToTypes` table
INGEST_METADATA_TYPE = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"


def main(job, sip_uuid, dc_path):
    # If there's no metadata, that's not an error, and just keep going
    if not os.path.exists(dc_path):
        job.pyprint("DC metadata not found; exiting", "(at", dc_path + ")")
        return 0

    job.pyprint("Loading DC metadata from", dc_path)
    with open(dc_path) as json_data:
        data = json.load(json_data)
    dc = models.DublinCore(
        metadataappliestoidentifier=sip_uuid,
        metadataappliestotype_id=INGEST_METADATA_TYPE,
    )
    for key, value in data.items():
        try:
            setattr(dc, key, value)
        except AttributeError:
            job.pyprint("Invalid DC attribute:", key, file=sys.stderr)

    dc.save()

    # ``dc.json`` was copied to ingest so the code above could read it, but we
    # don't need it anymore so we're removing it.
    try:
        job.pyprint('Removing "dc.json":', dc_path)
        os.remove(dc_path)
    except Exception as err:
        job.pyprint('Unable to remove "dc.json":', err)

    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                sip_uuid = job.args[1]
                dc_path = job.args[2]
                job.set_status(main(job, sip_uuid, dc_path))
