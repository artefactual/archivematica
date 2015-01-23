#!/usr/bin/python -OO

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
import os
import sys
import uuid
# archivematicaCommon
import databaseFunctions
import fileOperations

from django.db.models import Q
# dashboard
from main.models import Event, File

#"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%fileUUID%" "%filePath%"
SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]
fileUUID = sys.argv[4]
filePath = sys.argv[5]
date = sys.argv[6]

# Search for original file associated with preservation file given in filePath
filePathLike = filePath.replace(os.path.join(SIPDirectory, "objects", "manualNormalization", "preservation"), "%SIPDirectory%objects", 1)
i = filePathLike.rfind(".")
k = os.path.basename(filePath).rfind(".")
if i != -1 and k != -1:
    filePathLike = filePathLike[:i+1]
    # Matches "path/to/file/filename." Includes . so it doesn't false match foobar.txt when we wanted foo.txt
    filePathLike1 = filePathLike
    # Matches the exact filename.  For files with no extension.
    filePathLike2 = filePathLike[:-1]

try:
    path_condition = Q(currentlocation__startswith=filePathLike1) | Q(currentlocation=filePathLike2)
    f = File.objects.get(path_condition,
                         removedtime__isnull=True,
                         filegrpuse="original",
                         sip_id=SIPUUID)
except (File.DoesNotExist, File.MultipleObjectsReturned) as e:
    # Original file was not found, or there is more than one original file with
    # the same filename (differing extensions)
    # Look for a CSV that will specify the mapping
    csv_path = os.path.join(SIPDirectory, "objects", "manualNormalization",
        "normalization.csv")
    if os.path.isfile(csv_path):
        try:
            preservation_file = filePath[filePath.index('manualNormalization/preservation/'):]
        except ValueError:
            print >>sys.stderr, "{0} not in manualNormalization directory".format(filePath)
            exit(4)
        original = fileOperations.findFileInNormalizatonCSV(csv_path,
            "preservation", preservation_file, SIPUUID)
        if original is None:
            if isinstance(e, File.DoesNotExist):
                print >>sys.stderr, "No matching file for: {0}".format(
                    filePath.replace(SIPDirectory, "%SIPDirectory%"))
                exit(3)
            else:
                print >>sys.stderr, "Could not find {preservation_file} in {filename}".format(
                        preservation_file=preservation_file, filename=csv_path)
                exit(2)
        # If we found the original file, retrieve it from the DB
        f = File.objects.get(removedtime__isnull=True,
                             filegrpuse="original",
                             originallocation__endswith=original,
                             sip_id=SIPUUID)
    else:
        if isinstance(e, File.DoesNotExist):
            print >>sys.stderr, "No matching file for: ", filePath.replace(SIPDirectory, "%SIPDirectory%", 1)
            exit(3)
        elif isinstance(e, File.MultipleObjectsReturned):
            print >>sys.stderr, "Too many possible files for: ", filePath.replace(SIPDirectory, "%SIPDirectory%", 1)
            exit(2)

# We found the original file somewhere above, get the UUID and path
originalFileUUID = f.uuid
originalFilePath = f.currentlocation

print "matched: (%s) %s to (%s) %s" % (originalFileUUID, originalFilePath, fileUUID, filePath)
basename = os.path.basename(filePath)
i = basename.rfind(".")
dstFile = basename[:i] + "-" + fileUUID + basename[i:] 
dstDir = os.path.dirname(originalFilePath.replace("%SIPDirectory%", SIPDirectory, 1))
dst = os.path.join(dstDir, dstFile)
dstR = dst.replace(SIPDirectory, "%SIPDirectory%", 1)

if os.path.isfile(dst) or os.path.isdir(dst):
    print >>sys.stderr, "already exists:", dstR
    exit(2)

#Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
#see http://docs.python.org/2/library/os.html
os.rename(filePath, dst)
f.currentlocation = dstR
f.save()

try:
    # Normalization event already exists, so just update it
    # fileUUID, eventIdentifierUUID, eventType, eventDateTime, eventDetail
    # probably already correct, and we only set eventOutcomeDetailNote here
    Event.objects.filter(event_type="normalization", file_uuid=f).update(event_outcome_detail=dstR)
except Event.DoesNotExist:
    # No normalization event was created in normalize.py - probably manually
    # normalized during Ingest
    derivationEventUUID = str(uuid.uuid4())
    databaseFunctions.insertIntoEvents(
        fileUUID=originalFileUUID,
        eventIdentifierUUID=derivationEventUUID,
        eventType="normalization",
        eventDateTime=date,
        eventDetail="manual normalization",
        eventOutcome="",
        eventOutcomeDetailNote=dstR)

    # Add linking information between files
    # Assuming that if an event already exists, then the derivation does as well
    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=originalFileUUID,
        derivedFileUUID=fileUUID,
        relatedEventUUID=derivationEventUUID)

exit(0)
