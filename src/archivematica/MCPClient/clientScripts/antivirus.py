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
import multiprocessing
import os
import uuid
from collections.abc import Callable
from collections.abc import Collection
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache

import django

django.setup()
from clamav_client.scanner import Scanner
from clamav_client.scanner import get_scanner
from django.conf import settings as mcpclient_settings

from archivematica.archivematicaCommon.custom_handlers import get_script_logger
from archivematica.archivematicaCommon.databaseFunctions import EventInput
from archivematica.archivematicaCommon.databaseFunctions import insert_events
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.MCPClient.client.job import Job

logger = get_script_logger("archivematica.mcp.client.clamscan")


def concurrent_instances():
    return multiprocessing.cpu_count()


def normalize_uuid(value: object) -> str | None:
    """Return a canonical UUID string, or ``None`` for an invalid value."""
    if isinstance(value, uuid.UUID):
        return str(value)
    try:
        return str(uuid.UUID(str(value)))
    except (AttributeError, TypeError, ValueError):
        return None


@dataclass(frozen=True)
class AntivirusBatchData:
    """File metadata and virus-check state loaded for an antivirus batch."""

    file_sizes: Mapping[str, int | None]
    scanned_file_uuids: Collection[str]


def load_file_data(
    jobs: Collection[Job],
) -> AntivirusBatchData:
    """Load file sizes and previous virus checks for a job batch."""
    file_uuids: set[str] = set()
    for job in jobs:
        if len(job.args) <= 1:
            continue
        file_uuid = normalize_uuid(job.args[1])
        if file_uuid is not None:
            file_uuids.add(file_uuid)

    file_sizes = {
        str(file_uuid): size
        for file_uuid, size in File.objects.filter(uuid__in=file_uuids).values_list(
            "uuid", "size"
        )
    }
    scanned_file_uuids = {
        str(file_uuid)
        for file_uuid in Event.objects.filter(
            file_uuid_id__in=file_uuids, event_type="virus check"
        ).values_list("file_uuid_id", flat=True)
    }

    return AntivirusBatchData(
        file_sizes=file_sizes,
        scanned_file_uuids=scanned_file_uuids,
    )


def queue_event(
    file_uuid: str | uuid.UUID,
    date: str,
    scanner: Scanner | None,
    passed: bool | None,
    queue: list[EventInput],
) -> None:
    if passed is None or file_uuid == "None":
        return

    event_detail = ""
    if scanner is not None:
        info = scanner.info()  # This is cached.
        event_detail = f'program="{info.name}"; version="{info.version}"; virusDefinitions="{info.virus_definitions}"'

    outcome = "Pass" if passed else "Fail"
    logger.info("Recording new event for file %s (outcome: %s)", file_uuid, outcome)

    queue.append(
        EventInput(
            file_uuid=file_uuid,
            event_type="virus check",
            event_datetime=date,
            event_detail=event_detail,
            event_outcome=outcome,
        )
    )


# Map the backend names provided by the user in the configuration to their
# corresponding internal values used by the clamav_client package. If no valid
# backend is specified, default to "clamdscanner".
SCANNERS = {"clamscanner": "clamscan", "clamdscanner": "clamd"}
DEFAULT_SCANNER = "clamd"

# Predefined builders for each backend.
CONFIG_BUILDERS = {
    "clamd": lambda: {
        "backend": "clamd",
        "address": str(mcpclient_settings.CLAMAV_SERVER),
        "timeout": int(mcpclient_settings.CLAMAV_CLIENT_TIMEOUT),
        "stream": bool(mcpclient_settings.CLAMAV_PASS_BY_STREAM),
    },
    "clamscan": lambda: {
        "backend": "clamscan",
        "max_file_size": float(mcpclient_settings.CLAMAV_CLIENT_MAX_FILE_SIZE),
        "max_scan_size": float(mcpclient_settings.CLAMAV_CLIENT_MAX_SCAN_SIZE),
    },
}


def create_scanner() -> Scanner:
    """Return the ClamAV client configured by the user and found in the
    installation's environment variables. Clamdscanner may perform quicker
    than Clamscanner given a larger number of objects. Return clamdscanner
    object as a default if no other, or an incorrect value is specified.
    """
    choice = str(mcpclient_settings.CLAMAV_CLIENT_BACKEND).lower()
    backend_key = SCANNERS.get(choice)
    if backend_key is None:
        logger.warning(
            'Unexpected antivirus scanner (CLAMAV_CLIENT_BACKEND): "%s"; using "%s".',
            choice,
            DEFAULT_SCANNER,
        )
        backend_key = DEFAULT_SCANNER
    try:
        config = CONFIG_BUILDERS[backend_key]()
    except KeyError:
        raise ValueError(f"Unexpected backend configuration: {backend_key!r}")
    return get_scanner(config)


def get_size(
    file_uuid: str | uuid.UUID,
    path: str,
    file_sizes: Mapping[str, int | None],
) -> int | None:
    """Return a file size from batch data or the filesystem."""
    normalized_file_uuid = normalize_uuid(file_uuid)

    if normalized_file_uuid is not None:
        try:
            return file_sizes[normalized_file_uuid]
        except KeyError:
            # The file is not always represented in the database, such as
            # files outside of `objects/`.
            pass

    try:
        return os.path.getsize(path)
    except Exception:
        return None


def scan_file(
    event_queue: list[EventInput],
    file_uuid: str | uuid.UUID,
    path: str,
    date: str,
    *,
    batch_data: AntivirusBatchData,
    scanner_factory: Callable[[], Scanner] | None = None,
) -> int:
    """Scan one file, queue its PREMIS event, and return its workflow status."""
    normalized_file_uuid = normalize_uuid(file_uuid)
    if (
        normalized_file_uuid is not None
        and normalized_file_uuid in batch_data.scanned_file_uuids
    ):
        logger.info("Virus scan already performed, not running scan again")
        return 0

    scanner: Scanner | None = None
    passed: bool | None = False

    try:
        size = get_size(file_uuid, path, batch_data.file_sizes)
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
            scanner = scanner_factory() if scanner_factory else create_scanner()
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


def call(jobs: list[Job]) -> None:
    """Process a batch of antivirus jobs."""
    event_queue: list[EventInput] = []
    batch_data = load_file_data(jobs)

    # TODO: Scanner.info() caches ClamAV definition metadata, so scanner reuse
    # can record stale definitions if freshclam reloads them during a batch.
    @cache
    def scanner_factory() -> Scanner:
        return create_scanner()

    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(
                scan_file(
                    event_queue,
                    *job.args[1:],
                    batch_data=batch_data,
                    scanner_factory=scanner_factory,
                )
            )

    insert_events(event_queue)
