#!/usr/bin/env python2

import argparse
from lxml import etree
import os

# archivematicaCommon
from custom_handlers import get_script_logger

from assign_file_uuids import find_mets_file
import parse_mets_to_db

logger = get_script_logger("archivematica.mcp.client.parse_external_mets")


def parse_reingest_mets(job, transfer_uuid, transfer_path):
    # Parse METS to extract information needed by later microservices
    mets_path = find_mets_file(transfer_path)
    try:
        root = etree.parse(mets_path)
    except Exception:
        job.pyprint("Error parsing reingest METS", mets_path, " - skipping")
        logger.info(
            "Error parsing reingest mets %s - skipping", mets_path, exc_info=True
        )
        return

    # Get SIP UUID from METS name
    sip_uuid = os.path.basename(mets_path).replace("METS.", "").replace(".xml", "")
    # Note: Because DublinCore and PREMIS rights are not database-level foreign keys, this works even though the SIP may not exist yet
    parse_mets_to_db.parse_dc(job, sip_uuid, root)
    parse_mets_to_db.parse_rights(job, sip_uuid, root)


def main(job, transfer_uuid, transfer_path):
    # Parse all external METS files if they exist
    parse_reingest_mets(job, transfer_uuid, transfer_path)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("transfer_uuid", help="%SIPUUID%")
    parser.add_argument("transfer_path", help="%SIPDirectory%")

    for job in jobs:
        with job.JobContext(logger=logger):
            args = parser.parse_args(job.args[1:])

            job.set_status(main(job, args.transfer_uuid, args.transfer_path))
