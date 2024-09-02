#!/usr/bin/env python
#
# Collects characterization commands for the provided file, then either
# a) Inserts the tool's XML output into the database, or
# b) Prints the tool's stdout, for tools which do not output XML
#
# If a tool has no defined characterization commands, then the default
# will be run instead.
import argparse
import dataclasses
import multiprocessing
import uuid
from typing import List

import django

django.setup()

from client.job import Job
from databaseFunctions import insertIntoFPCommandOutput
from dicts import ReplacementDict
from dicts import replace_string_values
from django.conf import settings as mcpclient_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from executeOrRunSubProcess import executeOrRun
from fpr.models import FormatVersion
from fpr.models import FPRule
from lib import setup_dicts
from lxml import etree
from main.models import FPCommandOutput


@dataclasses.dataclass
class CharacterizeFileArgs:
    file_uuid: uuid.UUID
    sip_uuid: uuid.UUID


def concurrent_instances() -> int:
    return multiprocessing.cpu_count()


def main(job: Job, file_uuid: uuid.UUID, sip_uuid: uuid.UUID) -> int:
    setup_dicts(mcpclient_settings)

    failed = False

    # Check to see whether the file has already been characterized; don't try
    # to characterize it a second time if so.
    if FPCommandOutput.objects.filter(file_id=file_uuid).exists():
        return 0

    try:
        format = FormatVersion.active.get(fileformatversion__file_uuid=file_uuid)
    except (FormatVersion.DoesNotExist, ValidationError):
        rules = format = None

    if format:
        rules = FPRule.active.filter(format=format.uuid, purpose="characterization")

    # Characterization always occurs - if nothing is specified, get one or more
    # defaults specified in the FPR.
    if not rules:
        rules = FPRule.active.filter(purpose="default_characterization")

    for rule in rules:
        if (
            rule.command.script_type == "bashScript"
            or rule.command.script_type == "command"
        ):
            args = []
            command_to_execute = replace_string_values(
                rule.command.command, file_=file_uuid, sip=sip_uuid, type_="file"
            )
        else:
            rd = ReplacementDict.frommodel(file_=file_uuid, sip=sip_uuid, type_="file")
            args = rd.to_gnu_options()
            command_to_execute = rule.command.command

        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type,
            command_to_execute,
            arguments=args,
            capture_output=True,
        )

        job.write_output(stdout)
        job.write_error(stderr)

        if exitstatus != 0:
            job.write_error(
                f"Command {rule.command.description} failed with exit status {exitstatus}; stderr:"
            )
            failed = True
            continue
        # fmt/101 is XML - we want to collect and package any XML output, while
        # allowing other commands to execute without actually collecting their
        # output in the event that they are writing their output to disk.
        # FPCommandOutput can have multiple rows for a given file,
        # distinguished by the rule that produced it.
        if (
            rule.command.output_format
            and rule.command.output_format.pronom_id == "fmt/101"
        ):
            try:
                etree.fromstring(stdout.encode("utf8"))
                insertIntoFPCommandOutput(file_uuid, stdout, rule.uuid)
                job.write_output(
                    f'Saved XML output for command "{rule.command.description}" ({rule.command.uuid})'
                )
            except etree.XMLSyntaxError:
                failed = True
                job.write_error(
                    f'XML output for command "{rule.command.description}" ({rule.command.uuid}) was not valid XML; not saving to database'
                )
        else:
            job.write_error(
                f'Tool output for command "{rule.command.description}" ({rule.command.uuid}) is not XML; not saving to database'
            )

    if failed:
        return 255
    else:
        return 0


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Characterize file.")
    parser.add_argument("file_uuid", type=uuid.UUID)
    parser.add_argument("sip_uuid", type=uuid.UUID)

    return parser


def parse_args(parser: argparse.ArgumentParser, job: Job) -> CharacterizeFileArgs:
    namespace = parser.parse_args(job.args[1:])

    return CharacterizeFileArgs(**vars(namespace))


def call(jobs: List[Job]) -> None:
    parser = get_parser()

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parse_args(parser, job)
                job.set_status(main(job, args.file_uuid, args.sip_uuid))
