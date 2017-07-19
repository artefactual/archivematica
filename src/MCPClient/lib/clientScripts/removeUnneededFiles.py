#!/usr/bin/env python2

from __future__ import print_function
import os
import sys
import shutil

# databaseFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import fileWasRemoved

from django.conf import settings as mcpclient_settings


def remove_file(target_file, file_uuid):
    removableFiles = [e.strip() for e in mcpclient_settings.REMOVABLE_FILES.split(',')]
    basename = os.path.basename(target_file)
    if basename in removableFiles:
        print("Removing {filename} (UUID: {uuid})".format(uuid=file_uuid, filename=basename))
        try:
            os.remove(target_file)
        except OSError:
            shutil.rmtree(target_file)
        # Gearman passes parameters as strings, so None (NoneType) becomes
        # "None" (string)
        if file_uuid and file_uuid != "None":
            fileWasRemoved(file_uuid)


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.removeUnneededFiles")

    target = sys.argv[1]
    file_uuid = sys.argv[2]

    sys.exit(remove_file(target, file_uuid))
