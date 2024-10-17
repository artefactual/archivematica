#!/usr/bin/env python
import argparse
import dataclasses
import multiprocessing
import uuid
from typing import List
from typing import Optional

import django

django.setup()

from client.job import Job
from databaseFunctions import insertIntoEvents
from django.db import transaction
from django.utils import timezone
from executeOrRunSubProcess import executeOrRun
from fpr.models import FormatVersion
from fpr.models import IDCommand
from fpr.models import IDRule
from main.models import File
from main.models import FileFormatVersion
from main.models import FileID
from main.models import UnitVariable

SUCCESS = 0
ERROR = 255


@dataclasses.dataclass
class IdentifyFileFormatArgs:
    idcommand: str
    file_path: str
    file_uuid: str
    disable_reidentify: bool


def concurrent_instances() -> int:
    return multiprocessing.cpu_count()


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

    rd = {"%IDCommand%": str(value)}

    UnitVariable.objects.create(
        unituuid=unit.pk, variable="replacementDict", variablevalue=str(rd)
    )


def write_identification_event(
    file_uuid: str,
    command: IDCommand,
    format: Optional[str] = None,
    success: bool = True,
) -> None:
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
        format_name=format.format.description,
        format_version=version,
        format_registry_name=format_registry,
        format_registry_key=key,
    )


def _default_idcommand() -> IDCommand:
    """Retrieve the default ``fpr.IDCommand``.

    We only expect to find one command enabled/active.
    """
    return IDCommand.active.first()


def main(
    job: Job, enabled: str, file_path: str, file_uuid: str, disable_reidentify: bool
) -> int:
    enabled_bool = True if enabled == "True" else False
    if not enabled_bool:
        job.print_output("Skipping file format identification")
        return SUCCESS

    command = _default_idcommand()
    if command is None:
        job.write_error("Unable to determine IDCommand.\n")
        return ERROR

    command_uuid = command.uuid
    job.print_output("IDCommand:", command.description)
    job.print_output("IDCommand UUID:", command.uuid)
    job.print_output("IDTool:", command.tool.description)
    job.print_output("IDTool UUID:", command.tool.uuid)
    job.print_output(f"File: ({file_uuid}) {file_path}")

    file_ = File.objects.get(uuid=file_uuid)

    # If reidentification is disabled and a format identification event exists for this file, exit
    if (
        disable_reidentify
        and file_.event_set.filter(event_type="format identification").exists()
    ):
        job.print_output(
            "This file has already been identified, and re-identification is disabled. Skipping."
        )
        return SUCCESS

    # Save whether identification was enabled by the user for use in a later
    # chain.
    _save_id_preference(file_, enabled_bool)

    exitcode, output, err = executeOrRun(
        command.script_type,
        command.script,
        arguments=[file_path],
        printing=False,
        capture_output=True,
    )
    output = output.strip()

    if exitcode != 0:
        job.print_error(f"Error: IDCommand with UUID {command_uuid} exited non-zero.")
        job.print_error(f"Error: {err}")
        return ERROR

    job.print_output("Command output:", output)
    # PUIDs are the same regardless of tool, so PUID-producing tools don't have "rules" per se - we just
    # go straight to the FormatVersion table to see if there's a matching PUID
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

    (ffv, created) = FileFormatVersion.objects.get_or_create(
        file_uuid=file_, defaults={"format_version": format_version}
    )
    if not created:  # Update the version if it wasn't created new
        ffv.format_version = format_version
        ffv.save()
    job.print_output(f"{file_path} identified as a {format_version.description}")

    write_identification_event(file_uuid, command, format=format_version.pronom_id)
    write_file_id(file_uuid=file_uuid, format=format_version, output=output)

    return SUCCESS


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Identify file formats.")

    # Since AM19 the accepted values are "True" or "False" since the ability to
    # choose the command from the workflow has been removed. Instead, this
    # script will look up in FPR what's the preferred command.
    # This argument may be renamed later.
    parser.add_argument("idcommand", type=str, help="%IDCommand%")

    parser.add_argument("file_path", type=str, help="%relativeLocation%")
    parser.add_argument("file_uuid", type=str, help="%fileUUID%")
    parser.add_argument(
        "--disable-reidentify",
        action="store_true",
        help="Disable identification if it has already happened for this file.",
    )

    return parser


def parse_args(parser: argparse.ArgumentParser, job: Job) -> IdentifyFileFormatArgs:
    namespace = parser.parse_args(job.args[1:])

    return IdentifyFileFormatArgs(**vars(namespace))


def call(jobs: List[Job]) -> None:
    parser = get_parser()

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parse_args(parser, job)
                job.set_status(
                    main(
                        job,
                        args.idcommand,
                        args.file_path,
                        args.file_uuid,
                        args.disable_reidentify,
                    )
                )
