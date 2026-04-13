#!/usr/bin/env python

import django

django.setup()

from archivematica.dashboard.fpr.models import FPRule
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import FileFormatVersion
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client.job import Job


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
    current_location_s = _decode_binary_path(f.currentlocation)
    if not current_location_s:
        raise ValueError(f"File {f.uuid} has no currentlocation value")

    # Look for files in a directory that starts with the package name
    files = File.objects.filter(
        transfer=f.transfer,
        currentlocation__startswith=current_location_s,
        removedtime__isnull=True,
    ).exclude(uuid=f.uuid)
    # Check for unpacking events that reference the package
    if Event.objects.filter(
        file_uuid__in=files,
        event_type="unpacking",
        event_detail__contains=current_location_s,
    ).exists():
        return True
    return False


def _decode_binary_path(value: bytes | memoryview | None) -> str:
    if value is None:
        return ""

    if isinstance(value, memoryview):
        value = value.tobytes()

    return value.decode()


def main(job: Job, sip_uuid: str) -> int:
    transfer = Transfer.objects.get(uuid=sip_uuid)
    for f in transfer.file_set.filter(removedtime__isnull=True).iterator():
        if is_extractable(f) and not already_extracted(f):
            job.pyprint(
                _decode_binary_path(f.currentlocation),
                "is extractable and has not yet been extracted.",
            )
            return 0
    job.pyprint("No extractable files found.")
    return 1


def call(jobs: list[Job]) -> None:
    for job in jobs:
        with job.JobContext():
            job.set_status(main(job, job.args[1]))
