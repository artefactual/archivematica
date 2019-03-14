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
import uuid

import django
from django.db import transaction

django.setup()
from django.db.models import Q

# dashboard
from main.models import Event, File

# archivematicaCommon
import databaseFunctions
import fileOperations


def main(job):
    # "%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%fileUUID%" "%filePath%"
    # job.args[2] (SIPName) is unused.
    SIPUUID = job.args[1]
    SIPDirectory = job.args[3]
    fileUUID = job.args[4]
    filePath = job.args[5]
    date = job.args[6]

    # Search for original file associated with preservation file given in filePath
    filePathLike = filePath.replace(
        os.path.join(SIPDirectory, "objects", "manualNormalization", "preservation"),
        "%SIPDirectory%objects",
        1,
    )
    i = filePathLike.rfind(".")
    k = os.path.basename(filePath).rfind(".")
    if i != -1 and k != -1:
        filePathLike = filePathLike[: i + 1]
        # Matches "path/to/file/filename." Includes . so it doesn't false match foobar.txt when we wanted foo.txt
        filePathLike1 = filePathLike
        # Matches the exact filename.  For files with no extension.
        filePathLike2 = filePathLike[:-1]

    try:
        path_condition = Q(currentlocation__startswith=filePathLike1) | Q(
            currentlocation=filePathLike2
        )
        original_file = File.objects.get(
            path_condition,
            removedtime__isnull=True,
            filegrpuse="original",
            sip_id=SIPUUID,
        )
    except (File.DoesNotExist, File.MultipleObjectsReturned) as e:
        # Original file was not found, or there is more than one original file with
        # the same filename (differing extensions)
        # Look for a CSV that will specify the mapping
        csv_path = os.path.join(
            SIPDirectory, "objects", "manualNormalization", "normalization.csv"
        )
        if os.path.isfile(csv_path):
            try:
                preservation_file = filePath[
                    filePath.index("manualNormalization/preservation/") :
                ]
            except ValueError:
                job.print_error(
                    "{0} not in manualNormalization directory".format(filePath)
                )
                return 4
            original = fileOperations.findFileInNormalizationCSV(
                csv_path,
                "preservation",
                preservation_file,
                SIPUUID,
                printfn=job.pyprint,
            )
            if original is None:
                if isinstance(e, File.DoesNotExist):
                    job.print_error(
                        "No matching file for: {0}".format(
                            filePath.replace(SIPDirectory, "%SIPDirectory%")
                        )
                    )
                    return 3
                else:
                    job.print_error(
                        "Could not find {preservation_file} in {filename}".format(
                            preservation_file=preservation_file, filename=csv_path
                        )
                    )
                    return 2
            # If we found the original file, retrieve it from the DB
            original_file = File.objects.get(
                removedtime__isnull=True,
                filegrpuse="original",
                originallocation__endswith=original,
                sip_id=SIPUUID,
            )
        else:
            if isinstance(e, File.DoesNotExist):
                job.print_error(
                    "No matching file for: ",
                    filePath.replace(SIPDirectory, "%SIPDirectory%", 1),
                )
                return 3
            elif isinstance(e, File.MultipleObjectsReturned):
                job.print_error(
                    "Too many possible files for: ",
                    filePath.replace(SIPDirectory, "%SIPDirectory%", 1),
                )
                return 2

    # We found the original file somewhere above
    job.print_output(
        "Matched original file %s (%s) to  preservation file %s (%s)"
        % (original_file.currentlocation, original_file.uuid, filePath, fileUUID)
    )
    # Generate the new preservation path: path/to/original/filename-uuid.ext
    basename = os.path.basename(filePath)
    i = basename.rfind(".")
    dstFile = basename[:i] + "-" + fileUUID + basename[i:]
    dstDir = os.path.dirname(
        original_file.currentlocation.replace("%SIPDirectory%", SIPDirectory, 1)
    )
    dst = os.path.join(dstDir, dstFile)
    dstR = dst.replace(SIPDirectory, "%SIPDirectory%", 1)

    if os.path.exists(dst):
        job.print_error("already exists:", dstR)
        return 2

    # Rename the preservation file
    job.print_output("Renaming preservation file", filePath, "to", dst)
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
        job.print_output(
            "Updated the eventOutcomeDetailNote of an existing normalization"
            " Event for file {}. Not creating a Derivation object".format(fileUUID)
        )
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
            eventOutcomeDetailNote=dstR,
        )
        job.print_output(
            "Created a manual normalization Event for file {}.".format(
                original_file.uuid
            )
        )

        # Add linking information between files
        # Assuming that if an event already exists, then the derivation does as well
        databaseFunctions.insertIntoDerivations(
            sourceFileUUID=original_file.uuid,
            derivedFileUUID=fileUUID,
            relatedEventUUID=derivationEventUUID,
        )
        job.print_output(
            "Created a Derivation for original file {}, derived file {}, and"
            " event {}".format(original_file.uuid, fileUUID, derivationEventUUID)
        )

    return 0


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                job.set_status(main(job))
