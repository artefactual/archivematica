#!/usr/bin/env python

import os

import django
django.setup()
# dashboard
from fpr.models import FPRule
from main.models import FileFormatVersion, Transfer, File, Event


def is_extractable(f):
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


AM_DATE_DELIMITER = '-AM-DATE-SFX-'


def already_extracted(f):
    """
    Returns True if this package has already been extracted, False otherwise.
    """
    # Once extracted by Archivematica, the current location of a package will
    # have been changed (i.e., suffixed with a date string; see
    # ``extract_contents.py::temporary_directory``) so we must reconstruct
    # the previous "current" location of the package (as ``package_name``) by
    # removing this date suffix.
    package_name = f.currentlocation.split(AM_DATE_DELIMITER)[0]
    package_name_w_slash = os.path.join(package_name, '')
    # Look for files in a directory that starts with ``package_name``
    files = File.objects.filter(
        transfer=f.transfer,
        currentlocation__startswith=package_name_w_slash,
        removedtime__isnull=True).exclude(uuid=f.uuid)
    # Check for unpacking events that reference the package
    if Event.objects.filter(
            file_uuid__in=files,
            event_type='unpacking',
            event_detail__contains=package_name).exists():
        return True
    return False


def main(job, sip_uuid):
    transfer = Transfer.objects.get(uuid=sip_uuid)
    for f in transfer.file_set.filter(removedtime__isnull=True).iterator():
        if is_extractable(f) and not already_extracted(f):
            job.pyprint(f.currentlocation, 'is extractable and has not yet been extracted.')
            return 0
    job.pyprint('No extractable files found.')
    return 1


def call(jobs):
    for job in jobs:
        with job.JobContext():
            job.set_status(main(job, job.args[1]))
