#!/usr/bin/env python
import argparse
import os
import shutil
import sys

import django
import requests

django.setup()
from django.conf import settings as mcpclient_settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from archivematica.archivematicaCommon import storageService as storage_service
from archivematica.archivematicaCommon.archivematicaFunctions import (
    find_transfer_path_from_ingest,
)
from archivematica.archivematicaCommon.custom_handlers import get_script_logger
from archivematica.dashboard.main import models
from archivematica.search.service import setup_search_service_from_conf

logger = get_script_logger("archivematica.mcp.client.post_store_aip_hook")

COMPLETED = 0
NO_ACTION = 1
ERROR = 2


def find_transfer_ids_by_unit_uuid(unit_uuid: str) -> set[str]:
    """Find transfer IDs by looking up files associated with a unit UUID.

    Searches for files that belong to either the given transfer UUID or SIP UUID,
    then returns the transfer UUIDs of those files. This is useful for finding
    all transfers associated with a SIP during storage operations.

    :param str unit_uuid: UUID of a transfer or SIP to search for
    :return: Set of transfer UUIDs associated with files in the unit
    """
    condition = Q(transfer_id=unit_uuid) | Q(sip_id=unit_uuid)
    return {
        f[0] for f in models.File.objects.filter(condition).values_list("transfer_id")
    }


def delete_transfer_directory(job, sip_uuid):
    """Delete the transfer directory that sourced this SIP.

    This is only expected to work when the SIP was not arranged in backlog.
    """
    current_location = (
        models.File.objects.filter(
            removedtime__isnull=True,
            sip_id=sip_uuid,
            transfer__currentlocation__isnull=False,
        )
        .values_list("transfer__currentlocation", flat=True)
        .distinct()
        .get()
    )
    transfer_path = os.path.abspath(
        find_transfer_path_from_ingest(
            current_location, mcpclient_settings.SHARED_DIRECTORY
        )
    )
    if not transfer_path.startswith(mcpclient_settings.PROCESSING_DIRECTORY):
        raise Exception("Transfer directory was found in an unexpected location.")
    shutil.rmtree(transfer_path, ignore_errors=False)
    return transfer_path


def dspace_handle_to_archivesspace(job, sip_uuid):
    """Fetch the DSpace handle from the Storage Service and send to ArchivesSpace."""
    # Get association to ArchivesSpace if it exists
    try:
        digital_object = models.ArchivesSpaceDigitalObject.objects.get(sip_id=sip_uuid)
    except (models.ArchivesSpaceDigitalObject.DoesNotExist, ValidationError):
        job.pyprint("SIP", sip_uuid, "not associated with an ArchivesSpace component")
        return NO_ACTION
    job.pyprint(
        "Digital Object",
        digital_object.remoteid,
        "for SIP",
        digital_object.sip_id,
        "found",
    )
    logger.info(
        "Digital Object %s for SIP %s found",
        digital_object.remoteid,
        digital_object.sip_id,
    )

    # Get dspace handle from SS
    file_info = storage_service.get_file_info(uuid=sip_uuid)[0]
    try:
        handle = file_info["misc_attributes"]["handle"]
    except KeyError:
        job.pyprint("AIP has no DSpace handle stored")
        return NO_ACTION
    job.pyprint("DSpace handle:", handle)
    logger.info("DSpace handle: %s", handle)

    # POST Dspace handle to ArchivesSpace
    # Get ArchivesSpace config
    config = models.DashboardSetting.objects.get_dict("upload-archivesspace_v0.0")
    archivesspace_url = config["base_url"]

    # Log in
    url = archivesspace_url + "/users/" + config["user"] + "/login"
    params = {"password": config["passwd"]}
    logger.debug("Log in to ArchivesSpace URL: %s", url)
    response = requests.post(
        url, params=params, timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT
    )
    logger.debug("Response: %s %s", response, response.content)
    session_id = response.json()["session"]
    headers = {"X-ArchivesSpace-Session": session_id}

    # Get Digital Object from ArchivesSpace
    url = archivesspace_url + digital_object.remoteid
    logger.debug("Get Digital Object info URL: %s", url)
    response = requests.get(
        url, headers=headers, timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT
    )
    logger.debug("Response: %s %s", response, response.content)
    body = response.json()

    # Update
    url = archivesspace_url + digital_object.remoteid
    file_version = {
        "file_uri": handle,
        "use_statement": config["use_statement"],
        "xlink_show_attribute": config["xlink_show"],
        "xlink_actuate_attribute": config["xlink_actuate"],
    }
    body["file_versions"].append(file_version)
    logger.debug("Modified Digital Object: %s", body)
    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=mcpclient_settings.AGENTARCHIVES_CLIENT_TIMEOUT,
    )
    job.pyprint("Update response:", response, response.content)
    logger.debug("Response: %s %s", response, response.content)
    if response.status_code != 200:
        job.pyprint("Error updating", digital_object.remoteid)
        return ERROR
    return COMPLETED


def post_store_hook(job, sip_uuid):
    """
    Hook for doing any work after an AIP is stored successfully.
    """
    update_es = "transfers" in mcpclient_settings.SEARCH_ENABLED
    if update_es:
        search_service = setup_search_service_from_conf(mcpclient_settings)
    else:
        logger.info("Skipping indexing: Transfers indexing is currently disabled.")
        search_service = None

    # SIP ARRANGEMENT

    # Mark files in this SIP as in an AIP (aip_created)
    file_uuids = models.File.objects.filter(sip=sip_uuid).values_list("uuid", flat=True)
    models.SIPArrange.objects.filter(file_uuid__in=file_uuids).update(aip_created=True)

    # Check if any of component transfers are completely stored
    # TODO Storage service should index AIPs, knows when to update ES
    transfer_uuids = set(
        models.SIPArrange.objects.filter(file_uuid__in=file_uuids).values_list(
            "transfer_uuid", flat=True
        )
    )
    for transfer_uuid in transfer_uuids:
        job.pyprint("Checking if transfer", transfer_uuid, "is fully stored...")
        arranged_uuids = set(
            models.SIPArrange.objects.filter(
                transfer_uuid=transfer_uuid, aip_created=True
            ).values_list("file_uuid", flat=True)
        )
        backlog_uuids = set(
            models.File.objects.filter(transfer=transfer_uuid).values_list(
                "uuid", flat=True
            )
        )
        # If all backlog UUIDs have been arranged
        if arranged_uuids == backlog_uuids:
            job.pyprint(
                "Transfer",
                transfer_uuid,
                "fully stored, sending delete request to storage service, deleting from transfer backlog",
            )
            # Submit delete req to SS (not actually delete), remove from ES
            storage_service.request_file_deletion(
                uuid=str(transfer_uuid),
                user_id=0,
                user_email="archivematica system",
                reason_for_deletion="All files in Transfer are now in AIPs.",
            )
            if update_es:
                transfer_ids = find_transfer_ids_by_unit_uuid(transfer_uuid)
                search_service.delete_transfer_files(transfer_ids)

    # DSPACE HANDLE TO ARCHIVESSPACE
    dspace_handle_to_archivesspace(job, sip_uuid)

    # POST-STORE CALLBACK
    storage_service.post_store_aip_callback(str(sip_uuid))

    # When not using SIP arrangement, we perform best-effort deletion of the
    # original transfer directory under currentlyProcessing.
    if not transfer_uuids:
        try:
            transfer_dir = delete_transfer_directory(job, sip_uuid)
        except Exception as err:
            job.pyprint("Failed to delete transfer directory: ", err, file=sys.stderr)
            return
        job.pyprint("Transfer directory deleted: ", transfer_dir)


def call(jobs):
    parser = argparse.ArgumentParser()
    parser.add_argument("sip_uuid", help="%SIPUUID%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                job.set_status(post_store_hook(job, args.sip_uuid))
