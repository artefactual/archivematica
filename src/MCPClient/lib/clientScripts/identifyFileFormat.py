#!/usr/bin/python2

import argparse
import os
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun

path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
from fpr.models import IDCommand, IDRule, FormatVersion
from main.models import FileFormatVersion, File


def main(command_uuid, file_path, file_uuid):
    print "IDCommand UUID:", command_uuid
    print "File: ({}) {}".format(file_uuid, file_path)
    if command_uuid == "None":
        print "Skipping file format identification"
        return 0
    try:
        command = IDCommand.active.get(uuid=command_uuid)
    except IDCommand.DoesNotExist:
        sys.stderr.write("IDCommand with UUID {} does not exist.\n".format(command_uuid))
        return -1
    exitcode, output, _ = executeOrRun(command.script_type, command.script, arguments=[file_path], printing=False)
    output = output.strip()

    if exitcode != 0:
        print >>sys.stderr, 'Error: IDCommand with UUID {} exited non-zero.'.format(command_uuid)
        return -1

    print 'Command output:', output
    # PUIDs are the same regardless of tool, so PUID-producing tools don't have "rules" per se - we just
    # go straight to the FormatVersion table to see if there's a matching PUID
    try:
        if command.config == 'PUID':
            version = FormatVersion.active.get(pronom_id=output)
        else:
            rule = IDRule.active.get(command_output=output, command=command)
            version = rule.format
    except IDRule.DoesNotExist:
        print >>sys.stderr, 'Error: No FPR identification rule for tool output "{}" found'.format(output)
        return -1
    except IDRule.MultipleObjectsReturned:
        print >>sys.stderr, 'Error: Multiple FPR identification rules for tool output "{}" found'.format(output)
        return -1
    except FormatVersion.DoesNotExist:
        print >>sys.stderr, 'Error: No FPR format record found for PUID {}'.format(output)
        return -1

    # TODO shouldn't have to get File object - http://stackoverflow.com/questions/2846029/django-set-foreign-key-using-integer
    file_ = File.objects.get(uuid=file_uuid)
    (ffv, created) = FileFormatVersion.objects.get_or_create(file_uuid=file_, defaults={'format_version': version})
    if not created:  # Update the version if it wasn't created new
        ffv.format_version = version
        ffv.save()
    print "{} identified as a {}".format(file_path, version.description)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Identify file formats.')
    parser.add_argument('idcommand', type=str, help='%IDCommand%')
    parser.add_argument('file_path', type=str, help='%relativeLocation%')
    parser.add_argument('file_uuid', type=str, help='%fileUUID%')

    args = parser.parse_args()
    sys.exit(main(args.idcommand, args.file_path, args.file_uuid))
