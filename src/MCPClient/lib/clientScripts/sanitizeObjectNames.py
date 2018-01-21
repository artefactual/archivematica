#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
from __future__ import print_function
from itertools import chain
import logging
import sys
import os
import unicodedata

import django
django.setup()
# dashboard
from main.models import File, Directory, Transfer

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import updateFileLocation
from archivematicaFunctions import unicodeToStr
import sanitizeNames

logger = logging.getLogger()


def sanitize_object_names(objectsDirectory, sipUUID, date, groupType, groupSQL, sipPath):
    """Sanitize object names in a Transfer/SIP."""
    relativeReplacement = objectsDirectory.replace(sipPath, groupType, 1)  # "%SIPDirectory%objects/"

    # Get any ``Directory`` instances created for this transfer (if such exist)
    directory_mdls = []
    if groupSQL == 'transfer_id':
        transfer_mdl = Transfer.objects.get(uuid=sipUUID)
        if transfer_mdl.diruuids:
            directory_mdls = Directory.objects.filter(
                transfer=transfer_mdl).all()

    # Sanitize objects on disk
    sanitizations = sanitizeNames.sanitizeRecursively(objectsDirectory)
    for oldfile, newfile in sanitizations.items():
        logger.info('sanitizations: %s -> %s', oldfile, newfile)

    eventDetail = 'program="sanitizeNames"; version="' + sanitizeNames.VERSION + '"'

    # Update files in DB
    kwargs = {
        groupSQL: sipUUID,
        "removedtime__isnull": True,
    }
    file_mdls = File.objects.filter(**kwargs)
    # Iterate over ``File`` and ``Directory``
    for model in chain(file_mdls, directory_mdls):
        # Check all files to see if any parent directory had a sanitization event
        current_location = unicodeToStr(
            unicodedata.normalize('NFC', model.currentlocation)).replace(
                groupType, sipPath)
        sanitized_location = unicodeToStr(current_location)
        logger.info('Checking %s', current_location)

        # Check parent directories
        # Since directory keys are a mix of sanitized and unsanitized, this is
        # a little complicated
        # Directories keys are in the form sanitized/sanitized/unsanitized
        # When a match is found (eg 'unsanitized' -> 'sanitized') reset the
        # search.
        # This will find 'sanitized/unsanitized2' -> 'sanitized/sanitized2' on
        # the next pass
        # TODO This should be checked for a more efficient solution
        dirpath = sanitized_location
        while objectsDirectory in dirpath:  # Stay within unit
            if dirpath in sanitizations:  # Make replacement
                sanitized_location = sanitized_location.replace(
                    dirpath, sanitizations[dirpath])
                dirpath = sanitized_location  # Reset search
            else:  # Check next level up
                dirpath = os.path.dirname(dirpath)

        if current_location != sanitized_location:
            old_location = current_location.replace(
                objectsDirectory, relativeReplacement, 1)
            new_location = sanitized_location.replace(
                objectsDirectory, relativeReplacement, 1)
            kwargs = {
                'src': old_location,
                'dst': new_location,
                'eventType': 'name cleanup',
                'eventDateTime': date,
                'eventDetail': "prohibited characters removed:" + eventDetail,
                'fileUUID': None,
            }
            if groupType == "%SIPDirectory%":
                kwargs['sipUUID'] = sipUUID
            elif groupType == "%transferDirectory%":
                kwargs['transferUUID'] = sipUUID
            else:
                print("bad group type", groupType, file=sys.stderr)
                sys.exit(3)
            logger.info('Sanitized name: %s -> %s', old_location, new_location)
            print('Sanitized name:', old_location, " -> ", new_location)
            if isinstance(model, File):
                updateFileLocation(**kwargs)
            else:
                model.currentlocation = new_location
                model.save()
        else:
            logger.info('No sanitization for %s', current_location)
            print('No sanitization found for', current_location)


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.sanitizeObjectNames")

    objectsDirectory = sys.argv[1]  # directory to run sanitization on.
    sipUUID = sys.argv[2]  # %SIPUUID%
    date = sys.argv[3]  # %date%
    taskUUID = sys.argv[4]  # %taskUUID%, unused
    groupType = sys.argv[5]  # SIPDirectory or transferDirectory
    groupType = "%%%s%%" % (groupType)  # %SIPDirectory% or %transferDirectory%
    groupSQL = sys.argv[6]  # transfer_id or sip_id
    sipPath = sys.argv[7]  # %SIPDirectory%

    sanitize_object_names(objectsDirectory, sipUUID, date, groupType, groupSQL, sipPath)
