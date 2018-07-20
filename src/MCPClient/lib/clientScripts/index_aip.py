#!/usr/bin/env python2

from glob import glob
import os
import sys
import traceback

# dashboard
from main.models import UnitVariable

# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions
import storageService as storage_service
import identifier_functions

import django
django.setup()

from django.conf import settings as mcpclient_settings

logger = get_script_logger("archivematica.mcp.client.indexAIP")


def get_identifiers(job, sip_path):
    """Get additional identifiers to index."""
    identifiers = []

    # MODS
    mods_paths = glob('{}/submissionDocumentation/**/mods/*.xml'.format(sip_path))
    for mods in mods_paths:
        identifiers.extend(identifier_functions.extract_identifiers_from_mods(mods))

    # Islandora identifier
    islandora_path = glob('{}/submissionDocumentation/**/*-METS.xml'.format(sip_path))
    for mets in islandora_path:
        identifiers.extend(identifier_functions.extract_identifier_from_islandora(mets))

    job.pyprint('Indexing additional identifiers %s', identifiers)

    return identifiers


def index_aip(job):
    """ Write AIP information to ElasticSearch. """
    sip_uuid = job.args[1]  # %SIPUUID%
    sip_name = job.args[2]  # %SIPName%
    sip_path = job.args[3]  # %SIPDirectory%
    sip_type = job.args[4]  # %SIPType%

    if not mcpclient_settings.SEARCH_ENABLED:
        logger.info('Skipping indexing: indexing is currently disabled.')
        return 0

    elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
    client = elasticSearchFunctions.get_client()

    job.pyprint('SIP UUID:', sip_uuid)
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    job.pyprint('AIP info:', aip_info)
    aip_info = aip_info[0]

    mets_name = 'METS.{}.xml'.format(sip_uuid)
    mets_path = os.path.join(sip_path, mets_name)

    identifiers = get_identifiers(job, sip_path)

    # If this is an AIC, find the number of AIP stored in it and index that
    aips_in_aic = None
    if sip_type == "AIC":
        try:
            uv = UnitVariable.objects.get(unittype="SIP",
                                          unituuid=sip_uuid,
                                          variable="AIPsinAIC")
            aips_in_aic = uv.variablevalue
        except UnitVariable.DoesNotExist:
            pass

    job.pyprint('Indexing AIP info')
    # Delete ES index before creating new one if reingesting
    if 'REIN' in sip_type:
        job.pyprint('Deleting outdated entry for AIP and AIP files with UUID', sip_uuid, 'from archival storage')
        elasticSearchFunctions.delete_aip(client, sip_uuid)
        elasticSearchFunctions.delete_aip_files(client, sip_uuid)

    # Index AIP
    elasticSearchFunctions.index_aip(
        client,
        sip_uuid,
        sip_name,
        aip_info['current_full_path'],
        mets_path,
        size=aip_info['size'],
        aips_in_aic=aips_in_aic,
        identifiers=identifiers,
        encrypted=aip_info['encrypted'])

    # Index AIP files
    job.pyprint('Indexing AIP files')
    # Even though we treat MODS identifiers as SIP-level, we need to index them
    # here because the archival storage tab actually searches on the
    # aips/aipfile index.
    exitCode = elasticSearchFunctions.index_files(
        client,
        index='aips',
        type_='aipfile',
        uuid=sip_uuid,
        pathToArchive=sip_path,
        identifiers=identifiers,
        sipName=sip_name,
    )
    if exitCode == 1:
        job.pyprint('Error indexing AIP files', file=sys.stderr)
        return 1

    return 0


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
