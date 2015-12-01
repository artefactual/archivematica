#!/usr/bin/env python2

import os
import sys

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger
import databaseFunctions

logger = get_script_logger("archivematica.mcp.client.manualNormalizationRemoveMNDirectories")

SIPDirectory = sys.argv[1]
manual_normalization_dir = os.path.join(SIPDirectory, "objects", "manualNormalization")

errorCount = 0

def recursivelyRemoveEmptyDirectories(dir):
    error_count = 0
    for root, dirs, files in os.walk(dir,topdown=False):
       for directory in dirs:
            try:
                os.rmdir(os.path.join(root, directory))
            except OSError as e:
                print >>sys.stderr, "{0} could not be deleted: {1}".format(
                    directory, e.args)
                error_count+= 1
    return error_count;

if os.path.isdir(manual_normalization_dir):
    # Delete normalization.csv if present
    normalization_csv = os.path.join(manual_normalization_dir, 'normalization.csv')
    if os.path.isfile(normalization_csv):
        os.remove(normalization_csv)
        # Need SIP UUID to get file UUID to remove file in DB
        sipUUID = SIPDirectory[-37:-1] # Account for trailing /

        f = File.objects.get(removedtime__isnull=True,
                             originallocation__endswith='normalization.csv',
                             sip_id=sipUUID)
        databaseFunctions.fileWasRemoved(f.uuid)

    # Recursively delete empty manual normalization dir
    try:
        errorCount += recursivelyRemoveEmptyDirectories(manual_normalization_dir)
        os.rmdir(manual_normalization_dir)
    except OSError as e:
        print >>sys.stderr, "{0} could not be deleted: {1}".format(
            manual_normalization_dir, e.args)
        errorCount += 1

exit(errorCount)
