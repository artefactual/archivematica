#!/usr/bin/env python2
"""
Associate manually normalized preservation files with their originals.

Find the original file that matches this file by filename.
Rename the preservation file to be in the same directory as the original.
Generate a manual normalization event.
Add a derivative link.

:param fileUUID: UUID of the preservation file.
:param filePath: Path on disk of the preservation file.
"""

import os
import sys
import uuid

import django
django.setup()
from django.db.models import Q
# dashboard
from main.models import Event, File
# archivematicaCommon
from custom_handlers import get_script_logger
import databaseFunctions
import fileOperations

logger = get_script_logger("archivematica.mcp.client.manualNormalizationCreateMetadataAndRestructure")

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
    original_file = File.objects.get(path_condition,
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
        original_file = File.objects.get(removedtime__isnull=True,
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

# We found the original file somewhere above
print "Matched original file %s (%s) to  preservation file %s (%s)" % (original_file.currentlocation, original_file.uuid, filePath, fileUUID)
# Generate the new preservation path: path/to/original/filename-uuid.ext
basename = os.path.basename(filePath)
i = basename.rfind(".")
dstFile = basename[:i] + "-" + fileUUID + basename[i:]
dstDir = os.path.dirname(original_file.currentlocation.replace("%SIPDirectory%", SIPDirectory, 1))
dst = os.path.join(dstDir, dstFile)
dstR = dst.replace(SIPDirectory, "%SIPDirectory%", 1)

if os.path.exists(dst):
    print >>sys.stderr, "already exists:", dstR
    exit(2)

# Rename the preservation file
print 'Renaming preservation file', filePath, 'to', dst
os.rename(filePath, dst)
# Update the preservation file's location
File.objects.filter(uuid=fileUUID).update(currentlocation=dstR)

try:
    # Normalization event already exists, so just update it
    # fileUUID, eventIdentifierUUID, eventType, eventDateTime, eventDetail
    # probably already correct, and we only set eventOutcomeDetailNote here
    # Not using .filter().update() because that doesn't generate an exception
    e = Event.objects.get(event_type="normalization", file_uuid=original_file)
    e.event_outcome_detail = dstR
    e.save()
except Event.DoesNotExist:
    # No normalization event was created in normalize.py - probably manually
    # normalized during Ingest
    derivationEventUUID = str(uuid.uuid4())
    databaseFunctions.insertIntoEvents(
        fileUUID=original_file.uuid,
        eventIdentifierUUID=derivationEventUUID,
        eventType="normalization",
        eventDateTime=date,
        eventDetail="manual normalization",
        eventOutcome="",
        eventOutcomeDetailNote=dstR)

    # Add linking information between files
    # Assuming that if an event already exists, then the derivation does as well
    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=original_file.uuid,
        derivedFileUUID=fileUUID,
        relatedEventUUID=derivationEventUUID)

exit(0)
