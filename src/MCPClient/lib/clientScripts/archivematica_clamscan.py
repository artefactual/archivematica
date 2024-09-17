#!/usr/bin/env python
# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
import argparse
import multiprocessing
import os
import uuid

import django

django.setup()
from clamav_client.scanner import get_scanner
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoEvents
from django.conf import settings as mcpclient_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from main.models import Event
from main.models import File

logger = get_script_logger("archivematica.mcp.client.clamscan")


def concurrent_instances():
    return multiprocessing.cpu_count()


def file_already_scanned(file_uuid):
    return (
        file_uuid != "None"
        and Event.objects.filter(
            file_uuid_id=file_uuid, event_type="virus check"
        ).exists()
    )


def queue_event(file_uuid, date, scanner, passed, queue):
    if passed is None or file_uuid == "None":
        return

    event_detail = ""
    if scanner is not None:
        info = scanner.info()  # This is cached.
        event_detail = f'program="{info.name}"; version="{info.version}"; virusDefinitions="{info.virus_definitions}"'

    outcome = "Pass" if passed else "Fail"
    logger.info("Recording new event for file %s (outcome: %s)", file_uuid, outcome)

    queue.append(
        {
            "fileUUID": file_uuid,
            "eventIdentifierUUID": str(uuid.uuid4()),
            "eventType": "virus check",
            "eventDateTime": date,
            "eventDetail": event_detail,
            "eventOutcome": outcome,
        }
    )


def get_parser():
    """Return a ``Namespace`` with the parsed arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file_uuid", metavar="fileUUID")
    parser.add_argument("path", metavar="PATH", help="File or directory location")
    parser.add_argument("date", metavar="DATE")
    parser.add_argument(
        "task_uuid", metavar="taskUUID", help="Currently unused, feel free to ignore."
    )
    return parser


# Map user-provided backend names from configuration to the corresponding
# internal values used in the clamav_client package. Default to "clamscanner" if
# no valid backend is specified in the configuration.
SCANNERS = {"clamscanner": "clamscan", "clamdscanner": "clamd"}
DEFAULT_SCANNER = "clamdscanner"


def create_scanner():
    """Return the ClamAV client configured by the user and found in the
    installation's environment variables. Clamdscanner may perform quicker
    than Clamscanner given a larger number of objects. Return clamdscanner
    object as a default if no other, or an incorrect value is specified.
    """
    choice = str(mcpclient_settings.CLAMAV_CLIENT_BACKEND).lower()
    backend = SCANNERS.get(choice)
    if backend is None:
        logger.warning(
            'Unexpected antivirus scanner (CLAMAV_CLIENT_BACKEND): "%s"; using "%s".',
            choice,
            DEFAULT_SCANNER,
        )
        backend = SCANNERS[DEFAULT_SCANNER]
    if backend == "clamd":
        return get_scanner(
            {
                "backend": "clamd",
                "address": str(mcpclient_settings.CLAMAV_SERVER),
                "timeout": int(mcpclient_settings.CLAMAV_CLIENT_TIMEOUT),
                "stream": bool(mcpclient_settings.CLAMAV_PASS_BY_STREAM),
            }
        )
    if backend == "clamscan":
        return get_scanner(
            {
                "backend": "clamscan",
                "max_file_size": float(mcpclient_settings.CLAMAV_CLIENT_MAX_FILE_SIZE),
                "max_scan_size": float(mcpclient_settings.CLAMAV_CLIENT_MAX_SCAN_SIZE),
            }
        )
    raise ValueError("Unexpected backend configuration.")


def get_size(file_uuid, path):
    # We're going to see this happening when files are not part of `objects/`.
    if file_uuid != "None":
        try:
            return File.objects.get(uuid=file_uuid).size
        except (File.DoesNotExist, ValidationError):
            pass
    # Our fallback.
    try:
        return os.path.getsize(path)
    except Exception:
        return None


def scan_file(event_queue, file_uuid, path, date):
    if file_already_scanned(file_uuid):
        logger.info("Virus scan already performed, not running scan again")
        return 0

    scanner, passed = None, False

    try:
        size = get_size(file_uuid, path)
        if size is None:
            logger.error("Getting file size returned: %s", size)
            return 1

        max_file_size = mcpclient_settings.CLAMAV_CLIENT_MAX_FILE_SIZE * 1024 * 1024
        max_scan_size = mcpclient_settings.CLAMAV_CLIENT_MAX_SCAN_SIZE * 1024 * 1024

        valid_scan = True

        if size > max_file_size:
            logger.info(
                "File will not be scanned. Size %s bytes greater than scanner "
                "max file size %s bytes",
                size,
                max_file_size,
            )
            valid_scan = False
        elif size > max_scan_size:
            logger.info(
                "File will not be scanned. Size %s bytes greater than scanner "
                "max scan size %s bytes",
                size,
                max_scan_size,
            )
            valid_scan = False

        if valid_scan:
            scanner = create_scanner()
            info = scanner.info()
            logger.info(
                "Using scanner %s (%s - %s)",
                info.name,
                info.version,
                info.virus_definitions,
            )

            result = scanner.scan(path)
            passed, state, details = result.passed, result.state, result.details
        else:
            passed, state, details = None, None, None

    except Exception:
        logger.error("Unexpected error scanning file %s", path, exc_info=True)
        return 1
    else:
        # record pass or fail, but not None if the file hasn't
        # been scanned, e.g. Max File Size thresholds being too low.
        if passed is not None:
            logger.info("File %s scanned!", path)
            logger.debug("passed=%s state=%s details=%s", passed, state, details)
    finally:
        queue_event(file_uuid, date, scanner, passed, event_queue)

    # If True or None, then we have no error, the file can move through the
    # process as expected...
    return 1 if passed is False else 0


def call(jobs):
    event_queue = []

    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(scan_file(event_queue, *job.args[1:]))

    with transaction.atomic():
        for e in event_queue:
            insertIntoEvents(**e)
