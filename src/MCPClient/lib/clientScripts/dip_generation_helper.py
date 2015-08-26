#!/usr/bin/env python2
from __future__ import print_function
import argparse
import ast
import csv
import sys

# dashboard
from django.db.models import Q
from main import models

# archivematicaCommon
import archivesspace
import archivematicaFunctions

# initialize Django (required for Django 1.7)
import django
django.setup()

def create_archivesspace_client():
    """
    Create an ArchivesSpace client instance.
    """
    # TODO use same code as views_as.py?
    repl_dict = models.MicroServiceChoiceReplacementDic.objects.get(description='ArchivesSpace Config')
    config = ast.literal_eval(repl_dict.replacementdic)

    try:
        client = archivesspace.ArchivesSpaceClient(
            host=config['%host%'],
            port=config['%port%'],
            user=config['%user%'],
            passwd=config['%passwd%']
        )
    except archivesspace.AuthenticationError:
        print("Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings.")
        return None
    except archivesspace.ConnectionError:
        print("Unable to connect to ArchivesSpace server at the default location! Check administrative settings.")
        return None
    return client

def parse_archivesspaceids_csv(files):
    """
    Parse filename and reference ID from archivesspaceids.csv files

    :param files: List of paths to archivesspaceids.csv files
    :return: Dict with {filename: reference ID}
    """
    file_info = {}
    # SIP is last, so takes priority
    for csv_path in files:
        with open(csv_path, 'rbU') as f:
            reader = csv.reader(f)
            for row in reader:
                filename = row[0]
                ref_id = row[1]
                file_info[filename] = ref_id
    return file_info

def parse_archivesspace_ids(sip_path, sip_uuid):
    """
    Parse an archivesspaceids.csv to pre-populate the matching GUI.

    :param sip_path: Path to the SIP to check for an archivesspaceids.csv
    :param sip_uuid: UUID of the SIP to auto-populate ArchivesSpace IDs for
    :return: 0 on success, 1 on failure
    """
    # Check for archivesspaceids.csv
    csv_paths = archivematicaFunctions.find_metadata_files(sip_path, 'archivesspaceids.csv')
    if not csv_paths:
        print('No archivesspaceids.csv files found, exiting')
        return 0

    file_info = parse_archivesspaceids_csv(csv_paths)
    if not file_info:
        print('No information found in archivesspaceids.csv files')
        return 1
    print(file_info)

    # Create client
    client = create_archivesspace_client()
    if not client:
        return 1

    for filename, ref_id in file_info.items():
        # Get file object (for fileUUID, to see if in DIP)
        print(filename, ref_id, '%SIPLocation%' + filename)
        try:

            f = models.File.objects.get(
                Q(originallocation='%transferDirectory%' + filename) |
                Q(originallocation='%transferDirectory%objects/' + filename) |
                Q(originallocation='%SIPDirectory%' + filename) |
                Q(originallocation='%SIPDirectory%objects/' + filename),
                sip_id=sip_uuid
            )
        except models.File.DoesNotExist:
            print(filename, 'not found in database, skipping')
            continue
        except models.File.MultipleObjectsReturned:
            print('Multiple entries for', filename, 'found in database, skipping')
            continue
        print('File:', f)

        # Query ref_id to client for resource_id
        resource = client.find_by_field('fullrecord', ref_id)
        try:
            resource_id = resource[0]['id']
        except IndexError:
            print('ArchivesSpace did not return an ID for', ref_id)
            print('Returned', resource)
            continue
        print('Resource ID:', resource_id)

        # Add to ArchivesSpaceDIPObjectResourcePairing
        models.ArchivesSpaceDIPObjectResourcePairing.objects.create(
            dipuuid=sip_uuid,
            fileuuid=f.uuid,
            resourceid=resource_id,
        )

    # Check if any files were processed?
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse metadata for DIP helpers')
    parser.add_argument('--sipUUID', required=True, help='%SIPUUID%')
    parser.add_argument('--sipPath', required=True, help='%SIPDirectory%')
    args = parser.parse_args()

    # Return non-zero if any of the helpers fail
    rc = 0
    rc = rc or parse_archivesspace_ids(args.sipPath, args.sipUUID)
    # rc = rc or another_dip_helper(args.sipPath, args.sipUUID)

    sys.exit(rc)
