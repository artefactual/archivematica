#!/usr/bin/python2

from __future__ import print_function
import datetime
import os
import subprocess
import sys
from tempfile import gettempdir
from uuid import uuid4

# dashboard
from main.models import Derivation, File, FileFormatVersion
from fpr.models import FPRule

# archivematicaCommon
from dicts import ReplacementDict
from executeOrRunSubProcess import executeOrRun
import databaseFunctions
import fileOperations


def insert_transcription_event(status, file_uuid, rule, relative_location):
    outcome = "transcribed" if status is 0 else "not transcribed"

    tool = rule.command.tool
    event_detail = u"program={}; version={}; command=\"{}\"".format(tool.description, tool.version, rule.command.command.replace('"', r'\"'))

    event_uuid = str(uuid4())

    databaseFunctions.insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=event_uuid,
        eventType="transcription",
        eventDetail=event_detail,
        eventOutcome=outcome,
        eventOutcomeDetailNote=relative_location
    )

    return event_uuid


def insert_file_into_database(file_uuid, sip_uuid, event_uuid, rule, output_path, relative_path):
    transcription_uuid = str(uuid4())
    today = str(datetime.date.today())
    fileOperations.addFileToSIP(
        relative_path,
        transcription_uuid,
        sip_uuid,
        task_uuid,
        today,
        sourceType="creation",
        use="text/ocr"
    )

    fileOperations.updateSizeAndChecksum(
        transcription_uuid,
        output_path,
        today,
        str(uuid4())
    )

    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=file_uuid,
        derivedFileUUID=transcription_uuid,
        relatedEventUUID=event_uuid
    )


def fetch_rules_for(file_):
    try:
        format = FileFormatVersion.objects.get(file_uuid=file_)
        return FPRule.objects.filter(format=format.format_version,
                                     purpose='transcription')
    except FileFormatVersion.DoesNotExist:
        return []


def fetch_rules_for_derivatives(file_):
    derivs = Derivation.objects.filter(source_file=file_)
    for deriv in derivs:
        derived_file = deriv.derived_file
        # Don't bother OCRing thumbnails
        if derived_file.filegrpuse == 'thumbnail':
            continue

        rules = fetch_rules_for(derived_file)
        if rules:
            return (derived_file, rules)

    return None, []


def main(task_uuid, file_uuid):
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
        print('{} is not an original; not transcribing'.format(file_uuid), file=sys.stderr)
        return 0

    rules = fetch_rules_for(file_)
    if not rules:
        file_, rules = fetch_rules_for_derivatives(file_)

    if not rules:
        print('No rules found for file {} and its derivatives; not transcribing'.format(file_uuid), file=sys.stderr)
        return 0
    else:
        print('Transcribing {} derivative {}'.format(file_.filegrpuse, file_.uuid), file=sys.stderr)

    rd = ReplacementDict.frommodel(file_=file_, type_='file')

    for rule in rules:
        script = rule.command.command
        if rule.command.script_type in ('bashScript', 'command'):
            script, = rd.replace(script)
            args = []
        else:
            args = rd.to_gnu_options

        exitstatus, stdout, stderr = executeOrRun(rule.command.script_type,
                                                  script, arguments=args)
        if exitstatus != 0:
            succeeded = False


        output_path = rd.replace(rule.command.output_location)[0]
        relative_path = output_path.replace(rd['%SIPDirectory%'], '%SIPDirectory%')
        event = insert_transcription_event(exitstatus, file_uuid, rule, relative_path)

        if os.path.isfile(output_path):
            insert_file_into_database(file_uuid, rd['%SIPUUID%'], event, rule, output_path, relative_path)

    return 0 if succeeded else 1


if __name__ == '__main__':
    task_uuid = sys.argv[1]
    file_uuid = sys.argv[2]
    transcribe = sys.argv[3]

    if transcribe == 'False':
        print('Skipping transcription')
        sys.exit(0)

    sys.exit(main(task_uuid, file_uuid))
