#!/usr/bin/env python2
#
# Collects characterization commands for the provided file, then either
# a) Inserts the tool's XML output into the database, or
# b) Prints the tool's stdout, for tools which do not output XML
#
# If a tool has no defined characterization commands, then the default
# will be run instead (currently FITS).

from lxml import etree
import multiprocessing

import django

django.setup()
from django.db import transaction
from django.conf import settings as mcpclient_settings

# dashboard
from main.models import FPCommandOutput
from fpr.models import FPRule, FormatVersion

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import insertIntoFPCommandOutput
from dicts import replace_string_values, ReplacementDict

from lib import setup_dicts


def concurrent_instances():
    return multiprocessing.cpu_count()


def main(job, file_path, file_uuid, sip_uuid):
    setup_dicts(mcpclient_settings)

    failed = False

    # Check to see whether the file has already been characterized; don't try
    # to characterize it a second time if so.
    if FPCommandOutput.objects.filter(file_id=file_uuid).count() > 0:
        return 0

    try:
        format = FormatVersion.active.get(fileformatversion__file_uuid=file_uuid)
    except FormatVersion.DoesNotExist:
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
                "Command {} failed with exit status {}; stderr:".format(
                    rule.command.description, exitstatus
                )
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
                etree.fromstring(stdout)
                insertIntoFPCommandOutput(file_uuid, stdout, rule.uuid)
                job.write_output(
                    'Saved XML output for command "{}" ({})'.format(
                        rule.command.description, rule.command.uuid
                    )
                )
            except etree.XMLSyntaxError:
                failed = True
                job.write_error(
                    'XML output for command "{}" ({}) was not valid XML; not saving to database'.format(
                        rule.command.description, rule.command.uuid
                    )
                )
        else:
            job.write_error(
                'Tool output for command "{}" ({}) is not XML; not saving to database'.format(
                    rule.command.description, rule.command.uuid
                )
            )

    if failed:
        return 255
    else:
        return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                job.set_status(main(job, *job.args[1:]))
