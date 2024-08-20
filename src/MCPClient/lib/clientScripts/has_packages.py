#!/usr/bin/env python
from typing import List

import django

django.setup()

from client.job import Job
from fpr.models import FPRule
from main.models import Event
from main.models import File
from main.models import FileFormatVersion
from main.models import Transfer


def is_extractable(f: File) -> bool:
    """
    Returns True if this file can be extracted, False otherwise.
    """
    # Check if an extract FPRule exists
    try:
        format = f.fileformatversion_set.get().format_version
    except FileFormatVersion.DoesNotExist:
        return False

    extract_rules = FPRule.active.filter(purpose="extract", format=format)
    if extract_rules:
        return True
    else:
        return False


def already_extracted(f: File) -> bool:
    """
    Returns True if this package has already been extracted, False otherwise.
    """
    # Look for files in a directory that starts with the package name
    files = File.objects.filter(
        transfer=f.transfer,
        currentlocation__startswith=f.currentlocation.decode(),
        removedtime__isnull=True,
    ).exclude(uuid=f.uuid)
    # Check for unpacking events that reference the package
    if Event.objects.filter(
        file_uuid__in=files,
        event_type="unpacking",
        event_detail__contains=f.currentlocation.decode(),
    ).exists():
        return True
    return False


def main(job: Job, sip_uuid: str) -> int:
    transfer = Transfer.objects.get(uuid=sip_uuid)
    for f in transfer.file_set.filter(removedtime__isnull=True).iterator():
        if is_extractable(f) and not already_extracted(f):
            job.pyprint(
                f.currentlocation.decode(),
                "is extractable and has not yet been extracted.",
            )
            return 0
    job.pyprint("No extractable files found.")
    return 1


def call(jobs: List[Job]) -> None:
    for job in jobs:
        with job.JobContext():
            job.set_status(main(job, job.args[1]))
