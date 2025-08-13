#!/usr/bin/env python
import os
import sys
import time
import traceback
from glob import glob

import django
from django.core.exceptions import ValidationError

from archivematica.archivematicaCommon import identifier_functions
from archivematica.archivematicaCommon import storageService as storage_service
from archivematica.archivematicaCommon import version
from archivematica.archivematicaCommon.aip_mets_parser import AIPMETSParser
from archivematica.archivematicaCommon.archivematicaFunctions import get_dashboard_uuid
from archivematica.archivematicaCommon.custom_handlers import get_script_logger
from archivematica.archivematicaCommon.databaseFunctions import get_sip_identifiers
from archivematica.dashboard.main.models import UnitVariable
from archivematica.search.service import setup_search_service_from_conf

django.setup()

from django.conf import settings as mcpclient_settings

logger = get_script_logger("archivematica.mcp.client.indexAIP")


def get_identifiers(job, sip_path):
    """Get additional identifiers to index."""
    identifiers = []

    # MODS
    mods_paths = glob(f"{sip_path}/submissionDocumentation/**/mods/*.xml")
    for mods in mods_paths:
        identifiers.extend(identifier_functions.extract_identifiers_from_mods(mods))

    # Islandora identifier
    islandora_path = glob(f"{sip_path}/submissionDocumentation/**/*-METS.xml")
    for mets in islandora_path:
        identifiers.extend(identifier_functions.extract_identifier_from_islandora(mets))

    job.pyprint("Indexing additional identifiers %s", identifiers)

    return identifiers


def index_aip(job):
    """Write AIP information to ElasticSearch."""
    sip_uuid = job.args[1]  # %SIPUUID%
    sip_name = job.args[2]  # %SIPName%
    sip_staging_path = job.args[3]  # %SIPDirectory%
    sip_type = job.args[4]  # %SIPType%
    aip_location = job.args[5]  # %AIPsStore%%

    if "aips" not in mcpclient_settings.SEARCH_ENABLED:
        logger.info("Skipping indexing: AIPs indexing is currently disabled.")
        return 0

    location_description = storage_service.retrieve_storage_location_description(
        aip_location, logger
    )
    search_service = setup_search_service_from_conf(mcpclient_settings)
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    job.pyprint("AIP info:", aip_info)
    aip_info = aip_info[0]
    mets_staging_path = os.path.join(sip_staging_path, f"METS.{sip_uuid}.xml")
    identifiers = get_identifiers(job, sip_staging_path) + get_sip_identifiers(sip_uuid)
    # If this is an AIC, find the number of AIP stored in it and index that
    aips_in_aic = None
    if sip_type == "AIC":
        try:
            uv = UnitVariable.objects.get(
                unittype="SIP", unituuid=sip_uuid, variable="AIPsinAIC"
            )
            aips_in_aic = uv.variablevalue
        except (UnitVariable.DoesNotExist, ValidationError):
            pass
    # Delete ES index before creating new one if reingesting
    if "REIN" in sip_type:
        job.pyprint(
            "Deleting outdated entry for AIP and AIP files with UUID",
            sip_uuid,
            "from archival storage",
        )
        search_service.delete_aip(sip_uuid)
        search_service.delete_aip_files(sip_uuid)
    # Stop if METS file is not at staging path.
    if not os.path.exists(mets_staging_path):
        error_message = "METS file does not exist at: " + mets_staging_path
        logger.error(error_message)
        job.pyprint(error_message, file=sys.stderr)
        return 1

    parser = AIPMETSParser(mets_staging_path)

    job.pyprint("Indexing AIP and AIP files")
    job.pyprint("AIP UUID: " + sip_uuid)
    job.pyprint("Indexing AIP files ...")
    # Even though we treat MODS identifiers as SIP-level, we need to index them
    # here because the archival storage tab actually searches on the
    # aips/aipfile index.
    am_version = version.get_version()
    indexed_at = time.time()
    ret = search_service.index_aip(
        uuid=sip_uuid,
        aip_stored_path=aip_info["current_full_path"],
        parser=parser,
        name=sip_name,
        aip_size=aip_info["size"],
        am_version=am_version,
        indexed_at=indexed_at,
        identifiers=identifiers,
        aips_in_aic=aips_in_aic,
        encrypted=aip_info["encrypted"],
        location=location_description,
        dashboard_uuid=get_dashboard_uuid() or "",
    )
    if ret == 1:
        job.pyprint("Error indexing AIP and AIP files", file=sys.stderr)
    else:
        job.pyprint("Done.")
    return ret


def filter_status_code(status_code):
    """Force successful status code.

    When ``INDEX_AIP_CONTINUE_ON_ERROR`` is enabled the desire of the user is
    to continue processing the package at all costs. To achieve it, we return
    the exit code 179 - this ensure that the job is marked as failing while the
    processing is not interrupted.
    """
    if mcpclient_settings.INDEX_AIP_CONTINUE_ON_ERROR and status_code > 0:
        status_code = 179
    return status_code


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            try:
                status_code = index_aip(job)
            except Exception as err:
                # We want to capture any exception so ``filter_status_code``
                # makes the last call on what is the status returned.
                status_code = 1
                job.print_error(repr(err))
                job.print_error(traceback.format_exc())

            job.set_status(filter_status_code(status_code))
