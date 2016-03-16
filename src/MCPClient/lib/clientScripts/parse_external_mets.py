#!/usr/bin/python2

from __future__ import print_function
import argparse
from lxml import etree
import os
import sys

# archivematicaCommon
from custom_handlers import get_script_logger

from archivematicaAssignFileUUID import find_mets_file
import parse_mets_to_db

logger = get_script_logger('archivematica.mcp.client.parse_external_mets')

def parse_reingest_mets(transfer_uuid, transfer_path):
    # Parse METS to extract information needed by later microservices
    mets_path = find_mets_file(transfer_path)
    try:
        root = etree.parse(mets_path)
    except Exception:
        print('Error parsing reingest METS', mets_path, ' - skipping')
        logger.info('Error parsing reingest mets %s - skipping', mets_path, exc_info=True)
        return

    # Get SIP UUID from METS name
    sip_uuid = os.path.basename(mets_path).replace('METS.', '').replace('.xml', '')
    # Note: Because DublinCore and PREMIS rights are not database-level foreign keys, this works even though the SIP may not exist yet
    parse_mets_to_db.parse_dc(sip_uuid, root)
    parse_mets_to_db.parse_rights(sip_uuid, root)

def main(transfer_uuid, transfer_path):
    # Parse all external METS files if they exist
    parse_reingest_mets(transfer_uuid, transfer_path)

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('transfer_uuid', help='%SIPUUID%')
    parser.add_argument('transfer_path', help='%SIPDirectory%')
    args = parser.parse_args()

    sys.exit(main(args.transfer_uuid, args.transfer_path))
