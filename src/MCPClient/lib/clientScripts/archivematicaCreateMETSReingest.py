#!/usr/bin/env python2
from __future__ import print_function
import datetime
from lxml import etree
import os
import sys

import archivematicaXMLNamesSpace as ns
import archivematicaCreateMETS2 as createmets2
import archivematicaCreateMETSRights as createmetsrights
import archivematicaCreateMETSMetadataCSV as createmetscsv

# dashboard
from main import models


def update_header(root, now):
    """
    Update metsHdr to have LASTMODDATE.
    """
    metshdr = root.find('mets:metsHdr', namespaces=ns.NSMAP)
    metshdr.set('LASTMODDATE', now)
    return root


def update_dublincore(root, sip_uuid, now):
    """
    Add new dmdSec for updated Dublin Core info relating to entire SIP.
    """
    return root


def update_rights(root, sip_uuid, now):
    """
    Add rightsMDs for updated PREMIS Rights.
    """
    return root


def add_events(root, sip_uuid):
    """
    Add reingest events for all existing files.
    """
    return root


def add_new_files(root, sip_uuid, sip_dir, now):
    """
    Add new metadata files to structMap, fileSec.  Add new amdSecs??? What events?  Parse files to add metadata to METS.
    """
    return root


def update_mets(sip_dir, sip_uuid):
    old_mets_path = os.path.join(
        sip_dir,
        'objects',
        'submissionDocumentation',
        'METS.' + sip_uuid + '.xml')
    print('Looking for old METS at path', old_mets_path)
    # Discard whitespace now so when printing later formats correctly
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(old_mets_path, parser=parser)
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat('T')

    update_header(root, now)
    update_dublincore(root, sip_uuid, now)
    update_rights(root, sip_uuid, now)
    add_events(root, sip_uuid)
    add_new_files(root, sip_uuid, sip_dir, now)

    # Delete original METS

    return root

if __name__ == '__main__':
    tree = update_mets(*sys.argv[1:])
    tree.write('mets.xml', pretty_print=True)
