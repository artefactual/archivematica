#!/usr/bin/env python2

import sys
import subprocess
import os
import uuid

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import updateFileLocation
from archivematicaFunctions import unicodeToStr
import sanitizeNames

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.sanitizeObjectNames")

    objectsDirectory = sys.argv[1] #the directory to run sanitization on.
    sipUUID =  sys.argv[2]
    date = sys.argv[3]
    taskUUID = sys.argv[4]
    groupType = sys.argv[5]
    groupType = "%%%s%%" % (groupType)
    groupSQL = sys.argv[6]
    sipPath =  sys.argv[7] #the unit path
    groupID = sipUUID

    #relativeReplacement = "%sobjects/" % (groupType) #"%SIPDirectory%objects/"
    relativeReplacement = objectsDirectory.replace(sipPath, groupType, 1) #"%SIPDirectory%objects/"


    sanitizations = sanitizeNames.sanitizeRecursively(objectsDirectory)

    eventDetail= "program=\"sanitizeNames\"; version=\"" + sanitizeNames.VERSION + "\""
    for oldfile, newfile in sanitizations:
        if os.path.isfile(newfile):
            oldfile = oldfile.replace(objectsDirectory, relativeReplacement, 1)
            newfile = newfile.replace(objectsDirectory, relativeReplacement, 1)
            print oldfile, " -> ", newfile

            if groupType == "%SIPDirectory%":
                updateFileLocation(oldfile, newfile, "name cleanup", date, "prohibited characters removed:" + eventDetail, fileUUID=None, sipUUID=sipUUID)
            elif groupType == "%transferDirectory%":
                updateFileLocation(oldfile, newfile, "name cleanup", date, "prohibited characters removed:" + eventDetail, fileUUID=None, transferUUID=sipUUID)
            else:
                print >>sys.stderr, "bad group type", groupType
                exit(3)

        elif os.path.isdir(newfile):
            oldfile = oldfile.replace(objectsDirectory, relativeReplacement, 1) + "/"
            newfile = newfile.replace(objectsDirectory, relativeReplacement, 1) + "/"
            directoryContents = []

            kwargs = {
                "removedtime__isnull": True,
                "currentlocation__startswith": oldfile,
                groupSQL: groupID
            }
            files = File.objects.filter(**kwargs)

            print oldfile, " -> ", newfile

            for f in files:
                new_path = unicodeToStr(f.currentlocation).replace(oldfile, newfile, 1)
                updateFileLocation(f.currentlocation,
                                   new_path,
                                   fileUUID=f.uuid,
                                   # Don't create sanitization events for each
                                   # file, since it's only a parent directory
                                   # somewhere up that changed.
                                   # Otherwise, extra amdSecs will be generated
                                   # from the resulting METS.
                                   createEvent=False)
