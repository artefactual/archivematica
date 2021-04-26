#!/usr/bin/env python2
import argparse
import csv

# dashboard
from django.db.models import Q
from main import models

# archivematicaCommon
from custom_handlers import get_script_logger
import archivematicaFunctions

# Third party dependencies, alphabetical by import source
from agentarchives import archivesspace

# initialize Django (required for Django 1.7)
import django

django.setup()
from django.db import transaction

logger = get_script_logger("archivematica.mcp.client.moveTransfer")


def create_archivesspace_client():
    """
    Create an ArchivesSpace client instance.
    """
    # TODO use same code as views_as.py?
    config = models.DashboardSetting.objects.get_dict("upload-archivesspace_v0.0")

    try:
        client = archivesspace.ArchivesSpaceClient(
            host=config["base_url"],
            user=config["user"],
            passwd=config["passwd"],
            repository=config["repository"],
        )
    except archivesspace.AuthenticationError:
        logger.error(
            "Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings."
        )
        return None
    except archivesspace.ConnectionError:
        logger.error(
            "Unable to connect to ArchivesSpace server at the default location! Check administrative settings."
        )
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
        with open(csv_path, "rU") as f:
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
    csv_paths = archivematicaFunctions.find_metadata_files(
        sip_path, "archivesspaceids.csv"
    )
    if not csv_paths:
        logger.info("No archivesspaceids.csv files found, exiting")
        return 0

    file_info = parse_archivesspaceids_csv(csv_paths)
    if not file_info:
        logger.info("No information found in archivesspaceids.csv files")
        return 1

    logger.info("File info: %s", file_info)

    # Create client
    client = create_archivesspace_client()
    if not client:
        return 1

    for filename, ref_id in file_info.items():
        # Get file object (for fileUUID, to see if in DIP)
        logger.debug('Getting file object: filename="%s" ref_id="%s"', filename, ref_id)
        try:

            f = models.File.objects.get(
                Q(originallocation="%transferDirectory%" + filename)
                | Q(originallocation="%transferDirectory%objects/" + filename)
                | Q(originallocation="%SIPDirectory%" + filename)
                | Q(originallocation="%SIPDirectory%objects/" + filename),
                sip_id=sip_uuid,
            )
        except models.File.DoesNotExist:
            logger.error("%s not found in database, skipping", filename)
            continue
        except models.File.MultipleObjectsReturned:
            logger.error(
                "Multiple entries for %s found in database, skipping", filename
            )
            continue
        logger.debug("File: %s", f)

        # Query ref_id to client for resource_id
        resource = client.find_by_id("archival_objects", "ref_id", ref_id)
        try:
            resource_id = resource[0]["id"]
        except IndexError:
            logger.error("ArchivesSpace did not return an ID for %s", ref_id)
            logger.error("Returned %s", resource)
            continue
        logger.debug("Resource ID: %s", resource_id)

        # Add to ArchivesSpaceDIPObjectResourcePairing
        models.ArchivesSpaceDIPObjectResourcePairing.objects.create(
            dipuuid=sip_uuid, fileuuid=f.uuid, resourceid=resource_id
        )

    # Check if any files were processed?
    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="Parse metadata for DIP helpers")
    parser.add_argument("--sipUUID", required=True, help="%SIPUUID%")
    parser.add_argument("--sipPath", required=True, help="%SIPDirectory%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])

                # Return non-zero if any of the helpers fail
                rc = 0
                rc = rc or parse_archivesspace_ids(args.sipPath, args.sipUUID)
                # rc = rc or another_dip_helper(args.sipPath, args.sipUUID)

                job.set_status(rc)
