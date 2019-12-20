#!/usr/bin/env python2

import json
import sys

import django

django.setup()
from django.db import transaction

# dashboard
from main import models

FIELDS = (
    "title",
    "is_part_of",
    "creator",
    "subject",
    "description",
    "publisher",
    "contributor",
    "date",
    "type",
    "format",
    "identifier",
    "source",
    "relation",
    "language",
    "coverage",
    "rights",
)


def main(job, transfer_uuid, target_path):
    jsonified = {}
    try:
        dc = models.DublinCore.objects.get(metadataappliestoidentifier=transfer_uuid)
    except:  # There may not be any DC metadata for this transfer, and that's fine
        job.pyprint("No DC metadata found; skipping", file=sys.stderr)
        return 0
    for field in FIELDS:
        attr = getattr(dc, field)
        if attr:
            jsonified[field] = attr

    job.pyprint("Saving the following properties to:", target_path)
    job.pyprint(jsonified)

    with open(target_path, "w") as json_file:
        json.dump(jsonified, json_file)
    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                transfer_uuid = job.args[1]
                target_path = job.args[2]
                job.set_status(main(job, transfer_uuid, target_path))
