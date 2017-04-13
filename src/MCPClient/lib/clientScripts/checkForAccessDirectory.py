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
import os
import sys
from optparse import OptionParser

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import updateFileLocation
from fileOperations import rename

def something(SIPDirectory, accessDirectory, objectsDirectory, DIPDirectory, SIPUUID, date, copy=False):
    # exitCode = 435
    exitCode = 179
    print(SIPDirectory)
    # For every file, & directory Try to find the matching file & directory in the objects directory
    for (path, dirs, files) in os.walk(accessDirectory):
        for file in files:
            accessPath = os.path.join(path, file)
            objectPath = accessPath.replace(accessDirectory, objectsDirectory, 1)
            objectName = os.path.basename(objectPath)
            objectNameExtensionIndex = objectName.rfind(".")

            if objectNameExtensionIndex != -1:
                objectName = objectName[:objectNameExtensionIndex + 1]
                objectNameLike = os.path.join( os.path.dirname(objectPath), objectName).replace(SIPDirectory, "%SIPDirectory%", 1)

                files = File.objects.filter(removedtime__isnull=True,
                                            currentlocation__startswith=objectNameLike,
                                            sip_id=SIPUUID)
                if not files.exists():
                    print("No corresponding object for:", accessPath.replace(SIPDirectory, "%SIPDirectory%", 1), file=sys.stderr)
                    exitCode = 1
                update = []
                for objectUUID, objectPath in files.values_list('uuid', 'currentlocation'):
                    objectExtension = objectPath.replace(objectNameLike, "", 1)
                    print(objectName[objectNameExtensionIndex + 1:], objectExtension, "\t", end=' ')
                    if objectExtension.find(".") != -1:
                        continue
                    print(objectName[objectNameExtensionIndex + 1:], objectExtension, "\t", end=' ')
                    dipPath = os.path.join(DIPDirectory,  "objects", "%s-%s" % (objectUUID, os.path.basename(accessPath)))
                    if copy:
                        print("TODO - copy not supported yet")
                    else:
                        dest = dipPath
                        rename(accessPath, dest)

                        src = accessPath.replace(SIPDirectory, "%SIPDirectory%")
                        dst = dest.replace(SIPDirectory, "%SIPDirectory%")
                        update.append((src, dst))
                for src, dst in update:
                    eventDetail = ""
                    eventOutcomeDetailNote = "moved from=\"" + src + "\"; moved to=\"" + dst + "\""
                    updateFileLocation(src, dst, "movement", date, eventDetail, sipUUID=SIPUUID, eventOutcomeDetailNote = eventOutcomeDetailNote)
    return exitCode



if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.checkForAccessDirectory")

    parser = OptionParser()
    #'--SIPDirectory "%SIPDirectory%" --accessDirectory "objects/access/" --objectsDirectory "objects" --DIPDirectory "DIP" -c'
    parser.add_option("-s",  "--SIPDirectory", action="store", dest="SIPDirectory", default="")
    parser.add_option("-u",  "--SIPUUID", action="store", dest="SIPUUID", default="")
    parser.add_option("-a",  "--accessDirectory", action="store", dest="accessDirectory", default="")
    parser.add_option("-o",  "--objectsDirectory", action="store", dest="objectsDirectory", default="")
    parser.add_option("-d",  "--DIPDirectory", action="store", dest="DIPDirectory", default="")
    parser.add_option("-t",  "--date", action="store", dest="date", default="")
    parser.add_option('-c', '--copy', dest='copy', action='store_true')

    (opts, args) = parser.parse_args()

    SIPDirectory = opts.SIPDirectory
    accessDirectory = os.path.join(SIPDirectory, opts.accessDirectory)
    objectsDirectory = os.path.join(SIPDirectory, opts.objectsDirectory)
    DIPDirectory = os.path.join(SIPDirectory, opts.DIPDirectory)
    SIPUUID = opts.SIPUUID
    date = opts.date
    copy = opts.copy

    if not os.path.isdir(accessDirectory):
        print("no access directory in this sip")
        exit(0)


    try:
        if not os.path.isdir(DIPDirectory):
            os.mkdir(DIPDirectory)
        if not os.path.isdir(os.path.join(DIPDirectory, "objects")):
            os.mkdir(os.path.join(DIPDirectory, "objects"))
    except:
        print("error creating DIP directory")

    exitCode = something(SIPDirectory, accessDirectory, objectsDirectory, DIPDirectory, SIPUUID, date, copy)
    exit(exitCode)
