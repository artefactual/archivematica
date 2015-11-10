#!/usr/bin/env python2
from __future__ import print_function
import argparse
import os
import sys
import uuid

import metsrw

from main import models

import databaseFunctions

def get_db_objects(mets, transfer_uuid):
    """
    Get DB objects for files in METS.

    This also validates that files exist for each file asserted in the structMap

    :param mets: Parse METS file
    :return: Dict where key is the FSEntry and value is the DB object
    """
    # TODO does this assert that structMap files exist on disk? Does that need to be checked separately?
    mapping = {}
    for entry in mets.all_files():
        if entry.type == 'Directory':
            continue
        # Get DB entry
        # Assuming that Dataverse has a flat file structure, so a filename uniquely identifies a file.
        try:
            f = models.File.objects.get(originallocation__endswith=entry.path, transfer_id=transfer_uuid)
        except models.File.DoesNotExist:
            # Actual extracted folder likely has a different path than the presumed one in the METS. Search on basename
            print('Could not find', entry.path, 'in database')
            bname = os.path.basename(entry.path)
            print('Look for', bname)
            f = models.File.objects.get(originallocation__endswith=bname, transfer_id=transfer_uuid)
        mapping[entry] = f
    return mapping

def update_file_use(mapping):
    """
    Update the file's USE for files in mets.

    :param mets: Parse METS file
    :return: None
    """
    for entry, f in mapping.items():
        f.filegrpuse = entry.use
        print(entry.label, 'file group use set to', entry.use)
        f.save()

def add_dataverse_agent():
    """
    Add Dataverse agent
    """
    agent = None
    # TODO Get this from the Dataverse METS?
    agent = models.Agent.objects.create(
        identifiertype='URI',
        identifiervalue='',
        name='',
        agenttype='organization',
    )
    return agent

def create_derivatives(mapping, dataverse_agent):
    """
    Create derivatives for derived tabular data.
    """
    for entry, f in mapping.items():
        if entry.derived_from and entry.use == 'derivative':
            original_uuid = mapping[entry.derived_from].uuid
            event_uuid = uuid.uuid4()
            # Add event
            databaseFunctions.insertIntoEvents(
                original_uuid,
                eventIdentifierUUID=event_uuid,
                eventType="derivation",
                eventDateTime=None,  # From Dataverse?
                eventDetail="",  # From Dataverse?
                eventOutcome="",  # From Dataverse?
                eventOutcomeDetailNote=f.currentlocation,
                agents=[dataverse_agent.id],
            )
            # Add derivation
            databaseFunctions.insertIntoDerivations(
                sourceFileUUID=original_uuid,
                derivedFileUUID=f.uuid,
                relatedEventUUID=event_uuid,
            )
            print('Added derivation from', original_uuid, 'to', f.uuid)

def main(unit_path, unit_uuid):
    dataverse_mets_path = os.path.join(unit_path, 'metadata', 'METS.xml')
    mets = metsrw.METSDocument.fromfile(dataverse_mets_path)
    mapping = get_db_objects(mets, unit_uuid)

    update_file_use(mapping)
    agent = add_dataverse_agent()
    create_derivatives(mapping, agent)
    return 0

if __name__ == '__main__':
    print('Parse Dataverse METS')
    parser = argparse.ArgumentParser(description='Parse Dataverse METS file')
    parser.add_argument('transfer_dir', action='store', type=str, help="%SIPDirectory%")
    parser.add_argument('transfer_uuid', action='store', type=str, help="%SIPUUID%")
    args = parser.parse_args()

    sys.exit(main(args.transfer_dir, args.transfer_uuid))
