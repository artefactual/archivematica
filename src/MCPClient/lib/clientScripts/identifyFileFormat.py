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
from fpr.models import IDToolConfig, IDRule, FormatVersion
from main.models import FileFormatVersion, File


def main(id_toolconfig, file_path, file_uuid):
    print "IDToolConfig UUID:", id_toolconfig
    if id_toolconfig == "None":
        print "Skipping file format identification"
        return 0
    try:
        config = IDToolConfig.active.get(uuid=id_toolconfig)
    except IDToolConfig.DoesNotExist:
        sys.stderr.write("IDToolConfig with UUID {} does not exist.\n".format(id_toolconfig))
        return -1
    command = config.command
    print "IDCommand UUID:", command.uuid
    _, output, _ = executeOrRun(command.script_type, command.script, arguments=[file_path], printing=False)
    output = output.strip()
    print 'Command output:', output
    # PUIDs are the same regardless of tool, so PUID-producing tools don't have "rules" per se - we just
    # go straight to the FormatVersion table to see if there's a matching PUID
    try:
        if config.config == 'PUID':
            version = FormatVersion.active.get(pronom_id=output)
        else:
            version = IDRule.active.get(command_output=output, command=command.uuid)
            version = version.format
    except (FormatVersion.DoesNotExist, IDRule.DoesNotExist, IDRule.MultipleObjectsReturned) as e:
        print >>sys.stderr, 'Error:', e
        return -1
    # TODO shouldn't have to get File object - http://stackoverflow.com/questions/2846029/django-set-foreign-key-using-integer
    file_ = File.objects.get(uuid=file_uuid)
    FileFormatVersion.objects.create(file_uuid=file_, format_version=version)
    print "{} identified as a {}".format(file_path, version.description)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Identify file formats.')
    parser.add_argument('id_toolconfig', type=str, help='%IDCommand%')
    parser.add_argument('file_path', type=str, help='%relativeLocation%')
    parser.add_argument('file_uuid', type=str, help='%fileUUID%')

    args = parser.parse_args()
    sys.exit(main(args.id_toolconfig, args.file_path, args.file_uuid))
