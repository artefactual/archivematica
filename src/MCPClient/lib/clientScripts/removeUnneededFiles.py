#!/usr/bin/env python2

import os
import sys
import ntpath

# databaseFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import fileWasRemoved
from main.models import File

REMOVEABLE_FILES = ["Thumbs.db", "Icon", u"Icon\u000D"]

def remove_file(sip_obj_dir, sip_UUID):

    ### 1. Remove unneeded files from package.
    for dir_path, dir_name, filenames in os.walk(sip_obj_dir):
        for remove_name in REMOVEABLE_FILES:
            for filename in filenames:
                if remove_name == filename:
                    del_file = dir_path + '/' + filename
                    os.remove(del_file)
                    logger.debug('removeUnneededFiles file deleted: %s', del_file)

    ### 2. Insert removal notification into events database
    sip_files = File.objects.filter(sip=sip_UUID).values_list('uuid', 'currentlocation')
    remove_files = [file_UUID for file_UUID, current_location in sip_files if (ntpath.basename(current_location) in REMOVEABLE_FILES and file_UUID != 'None')]
    logger.debug('removeUnneededFiles db results :  %s', remove_files)
    for file_UUID in remove_files:
        fileWasRemoved(file_UUID)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.removeUnneededFiles")

    sip_obj_dir = sys.argv[1]
    sip_UUID = sys.argv[2]

    sys.exit(remove_file(sip_obj_dir, sip_UUID))

