#!/usr/bin/env python
"""MCPClient task for materializing a Storage Service transfer selection."""

import argparse
from collections.abc import Sequence
from typing import NoReturn
from typing import cast

import django
from django.core.exceptions import ValidationError

django.setup()

import archivematica.archivematicaCommon.storageService as storage_service
from archivematica.archivematicaCommon.transfer_source_retrieval import StorageService
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    TransferSourceRetrievalError,
)
from archivematica.archivematicaCommon.transfer_source_retrieval import (
    retrieve_transfer_source,
)
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client.job import Job


class JobArgumentParser(argparse.ArgumentParser):
    """Report parser failures as task failures instead of exiting the worker."""

    def error(self, message: str) -> NoReturn:
        raise TransferSourceRetrievalError(f"Invalid arguments: {message}")


def _parser() -> argparse.ArgumentParser:
    """Build the parser for arguments supplied by the retrieval workflow link."""
    parser = JobArgumentParser(
        description="Retrieve transfer contents from a Storage Service transfer source."
    )
    parser.add_argument("transfer_uuid", help="UUID of the Transfer row to update")
    parser.add_argument(
        "copy_source",
        help="Transfer-source path to copy, optionally prefixed with location UUID",
    )
    parser.add_argument(
        "copy_destination_relative",
        help="Destination path relative to the currently processing location",
    )
    parser.add_argument(
        "copied_path",
        help="Absolute path expected after Storage Service copy completes",
    )
    parser.add_argument(
        "processing_directory",
        help="Internal Archivematica processing directory",
    )
    parser.add_argument("shared_directory", help="Archivematica shared directory")
    return parser


def _transfer_exists(transfer_uuid: str) -> bool:
    """Validate the transfer UUID and check that its database row still exists."""
    try:
        return Transfer.objects.filter(uuid=transfer_uuid).exists()
    except ValidationError as err:
        raise TransferSourceRetrievalError(
            f"Invalid transfer UUID {transfer_uuid!r}: {err}"
        ) from err


def _update_transfer_location(transfer_uuid: str, current_location: str) -> None:
    """Publish the materialized path only after retrieval completes."""
    try:
        updated = Transfer.objects.filter(uuid=transfer_uuid).update(
            currentlocation=current_location
        )
    except ValidationError as err:
        raise TransferSourceRetrievalError(
            f"Invalid transfer UUID {transfer_uuid!r}: {err}"
        ) from err

    if updated != 1:
        raise TransferSourceRetrievalError(f"Transfer {transfer_uuid} was not found.")


def main(
    transfer_uuid: str,
    copy_source: str,
    copy_destination_relative: str,
    copied_path: str,
    processing_directory: str,
    shared_directory: str,
) -> int:
    """Retrieve one transfer selection and publish its processing location."""
    if not _transfer_exists(transfer_uuid):
        raise TransferSourceRetrievalError(f"Transfer {transfer_uuid} was not found.")

    result = retrieve_transfer_source(
        [copy_source],
        copy_destination_relative,
        copied_path,
        processing_directory,
        shared_directory,
        cast(StorageService, storage_service),
    )
    _update_transfer_location(transfer_uuid, result.current_location)

    return 0


def call(jobs: Sequence[Job]) -> None:
    """Run a batch of retrieval tasks using the standard MCPClient contract."""
    parser = _parser()

    for job in jobs:
        with job.JobContext():
            try:
                args = parser.parse_args(job.args[1:])
                job.set_status(
                    main(
                        args.transfer_uuid,
                        args.copy_source,
                        args.copy_destination_relative,
                        args.copied_path,
                        args.processing_directory,
                        args.shared_directory,
                    )
                )
            except TransferSourceRetrievalError as err:
                job.print_error(err)
                job.set_status(1)
