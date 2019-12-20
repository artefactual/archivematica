#!/usr/bin/env python2

import argparse
import os
import shutil

# fileOperations requires Django to be set up
import django
import scandir

django.setup()
from django.db import transaction

# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
import fileOperations


def restructureForComplianceFileUUIDsAssigned(
    job,
    unit_path,
    unit_uuid,
    unit_type="sip_id",
    unit_path_replacement="%SIPDirectory%",
):
    # Create required directories
    archivematicaFunctions.create_directories(
        REQUIRED_DIRECTORIES, unit_path, printing=True, printfn=job.pyprint
    )
    unit_path = os.path.join(unit_path, "")  # Ensure both end with /
    objects_path = os.path.join(unit_path, "objects", "")
    # Move everything else to the objects directory, updating DB with new path
    for entry in os.listdir(unit_path):
        entry_path = os.path.join(unit_path, entry)
        if os.path.isfile(entry_path) and entry not in OPTIONAL_FILES:
            # Move to objects
            src = os.path.join(unit_path, entry)
            dst = os.path.join(objects_path, entry)
            fileOperations.updateFileLocation2(
                src=src,
                dst=dst,
                unitPath=unit_path,
                unitIdentifier=unit_uuid,
                unitIdentifierType=unit_type,  # sipUUID or transferUUID
                unitPathReplaceWith=unit_path_replacement,
                printfn=job.pyprint,
            )
        if os.path.isdir(entry_path) and entry not in REQUIRED_DIRECTORIES:
            # Make directory at new location if not exists
            entry_objects_path = entry_path.replace(unit_path, objects_path)
            if not os.path.exists(entry_objects_path):
                job.pyprint("Creating directory:", entry_objects_path)
                os.mkdir(entry_objects_path)
            # Walk and move to objects dir, preserving directory structure
            # and updating the DB
            for dirpath, dirnames, filenames in scandir.walk(entry_path):
                # Create children dirs in new location, otherwise move fails
                for dirname in dirnames:
                    create_dir = os.path.join(dirpath, dirname).replace(
                        unit_path, objects_path
                    )
                    if not os.path.exists(create_dir):
                        job.pyprint("Creating directory:", create_dir)
                        os.makedirs(create_dir)
                # Move files
                for filename in filenames:
                    src = os.path.join(dirpath, filename)
                    dst = src.replace(unit_path, objects_path)
                    fileOperations.updateFileLocation2(
                        src=src,
                        dst=dst,
                        unitPath=unit_path,
                        unitIdentifier=unit_uuid,
                        unitIdentifierType=unit_type,  # sipUUID or transferUUID
                        unitPathReplaceWith=unit_path_replacement,
                        printfn=job.pyprint,
                    )
            # Delete entry_path if it exists (is empty dir)
            job.pyprint("Removing directory", entry_path)
            shutil.rmtree(entry_path)


def call(jobs):
    parser = argparse.ArgumentParser(description="Restructure SIP or Transfer.")
    parser.add_argument("target", help="%SIPDirectory%")
    parser.add_argument("sip_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                try:
                    restructureForComplianceFileUUIDsAssigned(
                        job, args.target, args.sip_uuid
                    )
                except fileOperations.UpdateFileLocationFailed as e:
                    job.set_status(e.code)
