#!/usr/bin/env python2

from __future__ import print_function
import ConfigParser
import os
import sys
import shutil

# databaseFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import fileWasRemoved
from main.models import File

def remove_file(sip_dir, sip_UUID):

    ### Read in configurable file exclusion list.
    clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)
    try:
        removableFiles = [e.strip() for e in config.get('MCPClient', 'removableFiles').split(',')]
    except ConfigParser.NoOptionError:
        removableFiles = ["Thumbs.db", "Icon", u"Icon\u000D", ".DS_Store"]

    ### 1. Remove unneeded files from package.
    for dir_path, dir_name, filenames in os.walk(sip_dir):
        for filename in filenames:
            if filename in removableFiles:
                del_file = os.path.join(dir_path, filename)
                try:
                    os.remove(del_file)
                except OSError:
                    shutil.rmtree(del_file)
                logger.debug('removeUnneededFiles file deleted: %s', del_file)

    ### 2. Insert removal notification into events database
    sip_files = File.objects.filter(sip=sip_UUID).values_list('uuid', 'currentlocation')
    remove_files = [file_UUID for file_UUID, current_location in sip_files if (os.path.basename(current_location) in removableFiles and file_UUID != 'None')]
    logger.debug('removeUnneededFiles db results :  %s', remove_files)
    for file_UUID in remove_files:
        fileWasRemoved(file_UUID)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.removeUnneededFiles")

    sip_dir = sys.argv[1]
    sip_UUID = sys.argv[2]

    sys.exit(remove_file(sip_dir, sip_UUID))

