#!/usr/bin/python2
#
# Collects characterization commands for the provided file, then either
# a) Inserts the tool's XML output into the database, or
# b) Prints the tool's stdout, for tools which do not output XML
#
# If a tool has no defined characterization commands, then the default
# will be run instead (currently FITS).
from __future__ import print_function
import os
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import insertIntoFPCommandOutput
from dicts import replace_string_values, ReplacementDict

path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

from fpr.models import FPRule, FormatVersion


def main(file_path, file_uuid, sip_uuid):
    failed = False

    try:
        format = FormatVersion.active.get(fileformatversion__file_uuid=file_uuid)
    except FormatVersion.DoesNotExist:
        rules = format = None

    if format:
        rules = FPRule.active.filter(format=format.uuid,
                                     purpose='characterization')

    # Characterization always occurs - if nothing is specified, get one or more
    # defaults specified in the FPR.
    if not rules:
        rules = FPRule.active.filter(purpose='default_characterization')

    for rule in rules:
        if rule.command.script_type == 'bashScript' or rule.command.script_type == 'command':
            args = []
            command_to_execute = replace_string_values(rule.command.command,
                                                       file_=file_uuid, sip=sip_uuid, type_='file')
        else:
            rd = ReplacementDict.frommodel(file_=file_uuid,
                                           sip=sip_uuid, type_='file')
            args = rd.to_gnu_options()
            command_to_execute = rule.command.command

        exitstatus, stdout, stderr = executeOrRun(rule.command.script_type,
                                                  command_to_execute,
                                                  arguments=args)
        if exitstatus != 0:
            print('Command {} failed with exit status {}; stderr:'.format(rule.command.description, exitstatus),
                stderr, file=sys.stderr)
            failed = True
            continue
        # fmt/101 is XML - we want to collect and package any XML output, while
        # allowing other commands to execute without actually collecting their
        # output in the event that they are writing their output to disk.
        # FPCommandOutput can have multiple rows for a given file,
        # distinguished by the rule that produced it.
        if rule.command.output_format and rule.command.output_format.pronom_id == 'fmt/101':
            insertIntoFPCommandOutput(file_uuid, stdout, rule.uuid)
            print('Saved XML output for command "{}" ({})'.format(rule.command.description, rule.command.uuid))
        else:
            # If the output isn't XML, print the stdout to the screen so it can
            # be monitored by the operator
            print(stdout)

    if failed:
        return -1
    else:
        return 0

if __name__ == '__main__':
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    sys.exit(main(file_path, file_uuid, sip_uuid))
