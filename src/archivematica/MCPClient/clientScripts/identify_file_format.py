#!/usr/bin/env python
import argparse
import dataclasses
import json
import uuid
from typing import Optional

import django

django.setup()

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from archivematica.archivematicaCommon.databaseFunctions import insertIntoEvents
from archivematica.archivematicaCommon.executeOrRunSubProcess import executeOrRun
from archivematica.dashboard.fpr.models import FormatVersion
from archivematica.dashboard.fpr.models import IDCommand
from archivematica.dashboard.fpr.models import IDRule
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import FileFormatVersion
from archivematica.dashboard.main.models import FileID
from archivematica.dashboard.main.models import UnitVariable
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts.file_identification import (
    IdentificationBackend,
)
from archivematica.MCPClient.clientScripts.file_identification import (
    IdentificationRequest,
)
from archivematica.MCPClient.clientScripts.file_identification import (
    IdentificationResult,
)
from archivematica.MCPClient.clientScripts.file_identification import (
    get_identification_backend,
)

SUCCESS = 0
ERROR = 255


@dataclasses.dataclass
class IdentifyFileFormatArgs:
    """Parsed arguments for one format-identification job."""

    idcommand: str
    file_path: str
    file_uuid: str
    disable_reidentify: bool


@dataclasses.dataclass
class PendingIdentification:
    """A prepared file awaiting batch identification."""

    job: Job
    args: IdentifyFileFormatArgs
    file: File


def _save_id_preference(file_: File, value: bool) -> None:
    """
    Saves whether file format identification is being used.

    This is necessary in order to allow post-extraction identification to work.
    The replacement dict will be saved to the special 'replacementDict' unit
    variable, which will be transformed back into a passVar when a new chain in
    the same unit is begun.
    """
    # The unit_uuid foreign key can point to a transfer or SIP, and this tool
    # runs in both.
    # Check the SIP first - if it hasn't been assigned yet, then this is being
    # run during the transfer.
    unit = file_.sip or file_.transfer

    if unit is None or unit.pk is None:
        return

    rd = {"%IDCommand%": str(value)}

    UnitVariable.objects.create(
        unituuid=unit.pk, variable="replacementDict", variablevalue=json.dumps(rd)
    )


def write_identification_event(
    file_uuid: str,
    command: IDCommand,
    format: Optional[str] = None,
    success: bool = True,
) -> None:
    event_detail_text = ""
    if command.tool is not None:
        event_detail_text = (
            f'program="{command.tool.description}"; version="{command.tool.version}"'
        )
    if success:
        event_outcome_text = "Positive"
    else:
        event_outcome_text = "Not identified"

    if not format:
        format = "No Matching Format"

    date = timezone.now()

    insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=str(uuid.uuid4()),
        eventType="format identification",
        eventDateTime=date,
        eventDetail=event_detail_text,
        eventOutcome=event_outcome_text,
        eventOutcomeDetailNote=format,
    )


def write_file_id(file_uuid: str, format: FormatVersion, output: str) -> None:
    """
    Write the identified format to the DB.

    :param str file_uuid: UUID of the file identified
    :param FormatVersion format: FormatVersion it was identified as
    :param str output: Text that generated the match
    """
    if format.pronom_id:
        format_registry = "PRONOM"
        key = format.pronom_id
    else:
        format_registry = "Archivematica Format Policy Registry"
        key = output

    # Sometimes, this is null instead of an empty string
    version = format.version or ""

    FileID.objects.create(
        file_id=file_uuid,
        format_name=format.format.description if format.format is not None else "",
        format_version=version,
        format_registry_name=format_registry,
        format_registry_key=key,
    )


def _default_idcommand() -> IDCommand | None:
    """Retrieve the default ``fpr.IDCommand``.

    We only expect to find one command enabled/active.
    """
    return IDCommand.active.first()


def _create_backend(command: IDCommand) -> IdentificationBackend:
    """Build the selected backend using MCPClient configuration."""

    return get_identification_backend(
        command,
        execute_command=executeOrRun,
        workers=settings.IDENTIFICATION_WORKERS,
    )


def _prepare_identification(
    job: Job,
    args: IdentifyFileFormatArgs,
    command: IDCommand,
) -> PendingIdentification | None:
    """Log and prepare one eligible file for batch identification."""

    tool = command.tool
    tool_uuid: str | uuid.UUID
    if tool is not None:
        tool_description = tool.description
        tool_uuid = tool.uuid
    else:
        tool_description = tool_uuid = "Unknown"
    job.print_output("IDCommand:", command.description)
    job.print_output("IDCommand UUID:", command.uuid)
    job.print_output("IDTool:", tool_description)
    job.print_output("IDTool UUID:", tool_uuid)
    job.print_output(f"File: ({args.file_uuid}) {args.file_path}")

    file_ = File.objects.get(uuid=args.file_uuid)

    # Skip files with an existing identification event when re-identification
    # is disabled.
    if (
        args.disable_reidentify
        and file_.event_set.filter(event_type="format identification").exists()
    ):
        job.print_output(
            "This file has already been identified, and re-identification is disabled. Skipping."
        )
        return None

    # Save whether identification was enabled by the user for use in a later
    # chain. Keep this write in a short transaction; identification itself can
    # be comparatively slow and must not hold a database transaction open.
    with transaction.atomic():
        _save_id_preference(file_, True)

    return PendingIdentification(job=job, args=args, file=file_)


def _save_identification_result(
    pending: PendingIdentification,
    command: IDCommand,
    result: IdentificationResult,
) -> int:
    """Persist and report one result, returning its Gearman job status."""

    job = pending.job
    file_path = pending.args.file_path
    file_uuid = pending.args.file_uuid

    if result.errors:
        for error in result.errors:
            job.print_error(error)
        return ERROR

    output = result.output
    if output is None:
        raise ValueError("Successful identification result is missing output")

    job.print_output("Command output:", output)
    # PUIDs are the same regardless of tool, so PUID-producing tools don't
    # have "rules" per se. Go straight to the FormatVersion table to see if
    # there is a matching PUID.
    try:
        if command.config == "PUID":
            format_version = FormatVersion.active.get(pronom_id=output)
        else:
            rule = IDRule.active.get(command_output=output, command=command)
            format_version = rule.format
    except IDRule.DoesNotExist:
        job.print_error(
            f'Error: No FPR identification rule for tool output "{output}" found'
        )
        write_identification_event(file_uuid, command, success=False)
        return ERROR
    except IDRule.MultipleObjectsReturned:
        job.print_error(
            f'Error: Multiple FPR identification rules for tool output "{output}" found'
        )
        write_identification_event(file_uuid, command, success=False)
        return ERROR
    except FormatVersion.DoesNotExist:
        job.print_error(f"Error: No FPR format record found for PUID {output}")
        write_identification_event(file_uuid, command, success=False)
        return ERROR

    ffv, created = FileFormatVersion.objects.get_or_create(
        file_uuid=pending.file, defaults={"format_version": format_version}
    )
    if not created:
        ffv.format_version = format_version
        ffv.save()
    job.print_output(f"{file_path} identified as a {format_version.description}")

    write_identification_event(file_uuid, command, format=format_version.pronom_id)
    write_file_id(file_uuid=file_uuid, format=format_version, output=output)

    return SUCCESS


def _identify_pending(
    pending_identifications: list[PendingIdentification],
    command: IDCommand,
) -> None:
    """Identify prepared files in one batch and finish their jobs."""

    backend = _create_backend(command)
    requests = [
        IdentificationRequest(path=pending.args.file_path)
        for pending in pending_identifications
    ]

    try:
        results = backend.identify_many(requests)
        if len(results) != len(requests):
            raise ValueError(
                "Identification backend returned "
                f"{len(results)} results for {len(requests)} requests"
            )
    except Exception as error:
        for pending in pending_identifications:
            with pending.job.JobContext():
                pending.job.print_error(
                    f"Error: Batch format identification failed: {error}"
                )
                pending.job.set_status(ERROR)
        return

    for pending, result in zip(pending_identifications, results):
        with pending.job.JobContext():
            with transaction.atomic():
                status = _save_identification_result(pending, command, result)
            pending.job.set_status(status)


def main(
    job: Job, enabled: str, file_path: str, file_uuid: str, disable_reidentify: bool
) -> int:
    """Identify one file through the batch backend contract."""

    enabled_bool = True if enabled == "True" else False
    if not enabled_bool:
        job.print_output("Skipping file format identification")
        return SUCCESS

    command = _default_idcommand()
    if command is None:
        job.write_error("Unable to determine IDCommand.\n")
        return ERROR

    args = IdentifyFileFormatArgs(
        idcommand=enabled,
        file_path=file_path,
        file_uuid=file_uuid,
        disable_reidentify=disable_reidentify,
    )
    pending = _prepare_identification(job, args, command)
    if pending is None:
        return SUCCESS

    result = _create_backend(command).identify_many(
        [IdentificationRequest(path=file_path)]
    )[0]
    with transaction.atomic():
        return _save_identification_result(pending, command, result)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Identify file formats.")

    # Since AM19 the accepted values are "True" or "False" since the ability to
    # choose the command from the workflow has been removed. Instead, this
    # script will look up in FPR what's the preferred command.
    # This argument may be renamed later.
    parser.add_argument("idcommand", type=str, help="%%IDCommand%%")

    parser.add_argument("file_path", type=str, help="%%relativeLocation%%")
    parser.add_argument("file_uuid", type=str, help="%%fileUUID%%")
    parser.add_argument(
        "--disable-reidentify",
        action="store_true",
        help="Disable identification if it has already happened for this file.",
    )

    return parser


def parse_args(parser: argparse.ArgumentParser, job: Job) -> IdentifyFileFormatArgs:
    namespace = parser.parse_args(job.args[1:])

    return IdentifyFileFormatArgs(**vars(namespace))


def call(jobs: list[Job]) -> None:
    """Prepare a Gearman job batch and identify eligible files together."""

    parser = get_parser()
    enabled_jobs: list[tuple[Job, IdentifyFileFormatArgs]] = []

    for job in jobs:
        with job.JobContext():
            args = parse_args(parser, job)
            if args.idcommand != "True":
                job.print_output("Skipping file format identification")
                job.set_status(SUCCESS)
                continue
            enabled_jobs.append((job, args))

    if not enabled_jobs:
        return

    command = _default_idcommand()
    if command is None:
        for job, _ in enabled_jobs:
            with job.JobContext():
                job.write_error("Unable to determine IDCommand.\n")
                job.set_status(ERROR)
        return

    pending_identifications = []
    for job, args in enabled_jobs:
        with job.JobContext():
            pending = _prepare_identification(job, args, command)
            if pending is None:
                job.set_status(SUCCESS)
                continue
            pending_identifications.append(pending)

    if pending_identifications:
        _identify_pending(pending_identifications, command)
