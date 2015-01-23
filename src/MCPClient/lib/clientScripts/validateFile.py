#!/usr/bin/python2
"""
Runs a validation command on the provided file, and generates an Event from
the results.

If a format has no defined validation commands, no command is run.
"""
from __future__ import print_function
import ast
import sys

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun
import databaseFunctions
from dicts import replace_string_values

# dashboard
from fpr.models import FPRule, FormatVersion


def main(file_path, file_uuid, sip_uuid):
    failed = False

    # Get file format
    try:
        fmt = FormatVersion.active.get(fileformatversion__file_uuid=file_uuid)
    except FormatVersion.DoesNotExist:
        rules = fmt = None

    if fmt:
        rules = FPRule.active.filter(format=fmt.uuid, purpose='validation')

    # Check for a default rule exists
    if not rules:
        rules = FPRule.active.filter(purpose='default_validation')

    for rule in rules:
        if rule.command.script_type in ('bashScript', 'command'):
            command_to_execute = replace_string_values(rule.command.command,
                file_=file_uuid, sip=sip_uuid, type_='file')
            args = []
        else:
            command_to_execute = rule.command.command
            args = [file_path]

        print('Running', rule.command.description)
        exitstatus, stdout, stderr = executeOrRun(rule.command.script_type,
            command_to_execute, arguments=args)
        if exitstatus != 0:
            print('Command {} failed with exit status {}; stderr:'.format(rule.command.description, exitstatus),
                stderr, file=sys.stderr)
            failed = True
            continue

        print('Command {} completed with output {}'.format(rule.command.description, stdout))

        # Parse output and generate an Event
        # Output is JSON in format:
        # { "eventOutcomeInformation": "pass",
        #   "eventOutcomeDetailNote": "format=\"JPEG\"; version=\"1.01\"; result=\"Well-Formed and valid\"" }
        # Or
        # { "eventOutcomeInformation": "fail",
        #   "eventOutcomeDetailNote": "format=\"Not detected\"; result=\"Not well-formed\"" }
        output = ast.literal_eval(stdout)
        event_detail = 'program="{tool.description}"; version="{tool.version}"'.format(tool=rule.command.tool)

        print('Creating validation event for {} ({})'.format(file_path, file_uuid))

        databaseFunctions.insertIntoEvents(
            fileUUID=file_uuid,
            eventType='validation',
            eventDetail=event_detail,
            eventOutcome=output.get('eventOutcomeInformation'),
            eventOutcomeDetailNote=output.get('eventOutcomeDetailNote'),
        )

    if failed:
        return -1
    else:
        return 0

if __name__ == '__main__':
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    sys.exit(main(file_path, file_uuid, sip_uuid))
