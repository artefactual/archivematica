#!/usr/bin/env python2
from __future__ import print_function
import argparse
import json
from django.utils import timezone
import os
import sys
import uuid

import metsrw

import django
django.setup()
from main import models

# archivematicaCommon
import databaseFunctions
from archivematicaFunctions import get_file_checksum

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
        if entry.type == 'Directory' or entry.label == 'dataset.json':
            continue
        # TODO remove this once RData files are returned
        if entry.path.endswith('.RData'):
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

def add_external_agents(unit_path):
    """
    Add external agent(s).

    :return: ID of the first agent, assuming that's the Dataverse agent.
    """
    agents_jsonfile = os.path.join(unit_path, 'metadata', 'agents.json')
    try:
        with open(agents_jsonfile, 'r') as f:
            agents_json = json.load(f)
    except (OSError, IOError):
        return None

    agent_id = None
    for agent in agents_json:
        a, created = models.Agent.objects.get_or_create(
            identifiertype=agent['agentIdentifierType'],
            identifiervalue=agent['agentIdentifierValue'],
            name=agent['agentName'],
            agenttype=agent['agentType'],
        )
        if created:
            print('Added agent', agent)
        else:
            print('Agent already exists', agent)
        agent_id = agent_id or a.id

    return agent_id

def create_derivatives(mapping, dataverse_agent_id):
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
                agents=[dataverse_agent_id],
            )
            # Add derivation
            databaseFunctions.insertIntoDerivations(
                sourceFileUUID=original_uuid,
                derivedFileUUID=f.uuid,
                relatedEventUUID=event_uuid,
            )
            print('Added derivation from', original_uuid, 'to', f.uuid)

def validate_checksums(mapping, unit_path):
    date = timezone.now().isoformat(' ')
    for entry, f in mapping.items():
        if entry.checksum and entry.checksumtype:
            print('Checking checksum', entry.checksum, 'for', entry.label)
            verify_checksum(
                file_uuid=f.uuid,
                path=f.currentlocation.replace('%transferDirectory%', unit_path),
                checksum=entry.checksum,
                checksumtype=entry.checksumtype,
                date=date,
            )

def verify_checksum(file_uuid, path, checksum, checksumtype, event_id=None, date=None):
    """
    Verify the checksum of a given file, and create a fixity event.

    :param str file_uuid: UUID of the file to verify
    :param str path: Path of the file to verify
    :param str checksum: Checksum to compare against
    :param str checksumtype: Type of the provided checksum (md5, sha256, etc)
    :param str event_id: Event ID
    :param str date: Date of the event
    """
    if event_id is None:
        event_id = str(uuid.uuid4())
    if date is None:
        date = timezone.now().isoformat(' ')

    checksumtype = checksumtype.lower()
    generated_checksum = get_file_checksum(path, checksumtype)
    event_detail = 'program="python"; module="hashlib.{}()"'.format(checksumtype)
    if checksum != generated_checksum:
        print('Checksum failed')
        event_outcome = "Fail"
        detail_note = 'Dataverse checksum %s verification failed' % checksum
    else:
        print('Checksum passed')
        event_outcome = "Pass"
        detail_note = 'Dataverse checksum %s verified' % checksum

    databaseFunctions.insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=event_id,
        eventType='fixity check',
        eventDateTime=date,
        eventDetail=event_detail,
        eventOutcome=event_outcome,
        eventOutcomeDetailNote=detail_note,
    )

def main(unit_path, unit_uuid):
    dataverse_mets_path = os.path.join(unit_path, 'metadata', 'METS.xml')
    mets = metsrw.METSDocument.fromfile(dataverse_mets_path)
    mapping = get_db_objects(mets, unit_uuid)

    update_file_use(mapping)
    agent = add_external_agents(unit_path)
    create_derivatives(mapping, agent)
    validate_checksums(mapping, unit_path)
    return 0

if __name__ == '__main__':
    print('Parse Dataverse METS')
    parser = argparse.ArgumentParser(description='Parse Dataverse METS file')
    parser.add_argument('transfer_dir', action='store', type=str, help="%SIPDirectory%")
    parser.add_argument('transfer_uuid', action='store', type=str, help="%SIPUUID%")
    args = parser.parse_args()

    sys.exit(main(args.transfer_dir, args.transfer_uuid))
