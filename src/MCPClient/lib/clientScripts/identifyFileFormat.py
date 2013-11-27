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
from main.models import FileFormatVersion, File, UnitVariable


def save_idtool(file_, value):
    """
    Saves the chosen ID tool's UUID in a unit variable, which allows it to be
    refetched by a later chain.

    This is necessary in order to allow post-extraction identification to work.
    The replacement dict will be saved to the special 'replacementDict' unit
    variable, which will be transformed back into a passVar when a new chain in
    the same unit is begun.
    """

    # The unit_uuid foreign key can point to a transfer or SIP, and this tool
    # runs in both.
    # Check the SIP first - if it hasn't been assigned yet, then this is being
    # run during the transfer.
    try:
        unit = file_.sip
    except:
        unit = file_.transfer

    rd = {
        "%IDCommand%": value
    }

    UnitVariable.objects.create(unituuid=unit.pk, variable='replacementDict', variablevalue=str(rd))

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

    # Save the selected ID command for use in a later chain
    file_ = File.objects.get(uuid=file_uuid)
    save_idtool(file_, command_uuid)

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
