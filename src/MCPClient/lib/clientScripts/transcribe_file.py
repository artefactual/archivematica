#!/usr/bin/env python
import argparse
import dataclasses
import multiprocessing
import os
import uuid
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

import django

django.setup()

import databaseFunctions
import fileOperations
from client.job import Job
from dicts import ReplacementDict
from django.conf import settings as mcpclient_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from executeOrRunSubProcess import executeOrRun
from fpr.models import FPRule
from lib import setup_dicts
from main.models import Derivation
from main.models import File
from main.models import FileFormatVersion


@dataclasses.dataclass
class TranscribeFileArgs:
    task_uuid: uuid.UUID
    file_uuid: uuid.UUID


def concurrent_instances() -> int:
    return multiprocessing.cpu_count()


def insert_transcription_event(
    status: int, file_uuid: uuid.UUID, rule: FPRule, relative_location: str
) -> str:
    outcome = "transcribed" if status == 0 else "not transcribed"

    tool = rule.command.tool
    event_detail = 'program={}; version={}; command="{}"'.format(
        tool.description, tool.version, rule.command.command.replace('"', r"\"")
    )

    event_uuid = str(uuid.uuid4())

    databaseFunctions.insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=event_uuid,
        eventType="transcription",
        eventDetail=event_detail,
        eventOutcome=outcome,
        eventOutcomeDetailNote=relative_location,
    )

    return event_uuid


def insert_file_into_database(
    task_uuid: uuid.UUID,
    file_uuid: uuid.UUID,
    sip_uuid: str,
    event_uuid: str,
    output_path: str,
    relative_path: str,
) -> None:
    transcription_uuid = str(uuid.uuid4())
    today = timezone.now()
    fileOperations.addFileToSIP(
        relative_path,
        transcription_uuid,
        sip_uuid,
        task_uuid,
        today,
        sourceType="creation",
        use="text/ocr",
    )

    fileOperations.updateSizeAndChecksum(
        transcription_uuid, output_path, today, str(uuid.uuid4())
    )

    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=file_uuid,
        derivedFileUUID=transcription_uuid,
        relatedEventUUID=event_uuid,
    )


def fetch_rules_for(file_: File) -> Sequence[FPRule]:
    try:
        format = FileFormatVersion.objects.get(file_uuid=file_)
        result: Sequence[FPRule] = FPRule.active.filter(
            format=format.format_version, purpose="transcription"
        )
        return result
    except (FileFormatVersion.DoesNotExist, ValidationError):
        return []


def fetch_rules_for_derivatives(file_: File) -> Tuple[Optional[File], Sequence[FPRule]]:
    derivs = Derivation.objects.filter(source_file=file_)
    for deriv in derivs:
        derived_file = deriv.derived_file
        # Don't bother OCRing thumbnails
        if derived_file.filegrpuse == "thumbnail":
            continue

        rules = fetch_rules_for(derived_file)
        if rules:
            return (derived_file, rules)

    return None, []


def main(job: Job, task_uuid: uuid.UUID, file_uuid: uuid.UUID) -> int:
    setup_dicts(mcpclient_settings)

    succeeded = True

    file_ = File.objects.get(uuid=file_uuid)

    # Normally we don't transcribe derivatives (access copies, preservation copies);
    # however, some useful transcription tools can't handle some formats that
    # are common as the primary copies. For example, tesseract can't handle JPEG2000.
    # If there are no rules for the primary format passed in, try to look at each
    # derivative until a transcribable derivative is found.
    #
    # Skip derivatives to avoid double-scanning them; only look at them as a fallback.
    if file_.filegrpuse != "original":
        job.print_error(f"{file_uuid} is not an original; not transcribing")
        return 0

    rules = fetch_rules_for(file_)
    if not rules:
        file_, rules = fetch_rules_for_derivatives(file_)

    if not rules:
        job.print_error(
            f"No rules found for file {file_uuid} and its derivatives; not transcribing"
        )
        return 0
    else:
        if file_.filegrpuse == "original":
            noun = "original"
        else:
            noun = file_.filegrpuse + " derivative"
        job.print_error(f"Transcribing {noun} {file_.uuid}")

    rd = ReplacementDict.frommodel(file_=file_, type_="file")

    for rule in rules:
        script = rule.command.command
        if rule.command.script_type in ("bashScript", "command"):
            (script,) = rd.replace(script)
            args = []
        else:
            args = rd.to_gnu_options()

        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type, script, arguments=args, capture_output=True
        )
        job.write_output(stdout)
        job.write_error(stderr)
        if exitstatus != 0:
            succeeded = False

        output_path = rd.replace(rule.command.output_location)[0]
        relative_path = output_path.replace(rd["%SIPDirectory%"], "%SIPDirectory%")
        event = insert_transcription_event(exitstatus, file_uuid, rule, relative_path)

        if os.path.isfile(output_path):
            insert_file_into_database(
                task_uuid,
                file_uuid,
                rd["%SIPUUID%"],
                event,
                output_path,
                relative_path,
            )

    return 0 if succeeded else 1


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe file.")
    parser.add_argument("task_uuid", type=uuid.UUID)
    parser.add_argument("file_uuid", type=uuid.UUID)

    return parser


def parse_args(parser: argparse.ArgumentParser, job: Job) -> TranscribeFileArgs:
    namespace = parser.parse_args(job.args[1:])

    return TranscribeFileArgs(**vars(namespace))


def call(jobs: List[Job]) -> None:
    parser = get_parser()

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parse_args(parser, job)

                job.set_status(main(job, args.task_uuid, args.file_uuid))
