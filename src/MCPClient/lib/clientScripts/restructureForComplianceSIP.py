#!/usr/bin/python2 -OO

import argparse
import os
import shutil
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
from archivematicaFunctions import REQUIRED_DIRECTORIES, OPTIONAL_FILES
import fileOperations


def restructureForComplianceFileUUIDsAssigned(unit_path, unit_uuid, unit_type='sipUUID', unit_path_replacement='%SIPDirectory%'):
    # Create required directories
    archivematicaFunctions.create_directories(REQUIRED_DIRECTORIES, unit_path, printing=True)
    unit_path = os.path.join(unit_path, '')  # Ensure both end with /
    objects_path = os.path.join(unit_path, 'objects', '')
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
                unitIdentifierType=unit_type, # sipUUID or transferUUID
                unitPathReplaceWith=unit_path_replacement)
        if os.path.isdir(entry_path) and entry not in REQUIRED_DIRECTORIES:
            # Make directory at new location if not exists
            entry_objects_path = entry_path.replace(unit_path, objects_path)
            if not os.path.exists(entry_objects_path):
                print 'Creating directory:', entry_objects_path
                os.mkdir(entry_objects_path)
            # Walk and move to objects dir, preserving directory structure
            # and updating the DB
            for dirpath, dirnames, filenames in os.walk(entry_path):
                # Create children dirs in new location, otherwise move fails
                for dirname in dirnames:
                    create_dir = os.path.join(dirpath, dirname).replace(unit_path, objects_path)
                    if not os.path.exists(create_dir):
                        print 'Creating directory:', create_dir
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
                        unitIdentifierType=unit_type, # sipUUID or transferUUID
                        unitPathReplaceWith=unit_path_replacement)
            # Delete entry_path if it exists (is empty dir)
            print 'Removing directory', entry_path
            shutil.rmtree(entry_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Restructure SIP or Transfer.')
    parser.add_argument('target', help='%SIPDirectory%')
    parser.add_argument('sip_uuid', help='%SIPUUID%')
    args = parser.parse_args()

    restructureForComplianceFileUUIDsAssigned(args.target, args.sip_uuid)


