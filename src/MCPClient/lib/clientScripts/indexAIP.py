#!/usr/bin/env python2

from __future__ import print_function
from glob import glob
import os
import sys

import django
django.setup()
# dashboard
from main.models import UnitVariable

# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions
import storageService as storage_service
from identifier_functions import extract_identifiers_from_mods

from config import settings


def list_mods(sip_path):
    return glob('{}/submissionDocumentation/**/mods/*.xml'.format(sip_path))


def index_aip():
    """ Write AIP information to ElasticSearch. """
    sip_uuid = sys.argv[1]  # %SIPUUID%
    sip_name = sys.argv[2]  # %SIPName%
    sip_path = sys.argv[3]  # %SIPDirectory%
    sip_type = sys.argv[4]  # %SIPType%

    # Check if Elasticsearch is enabled and exit otherwise
    indexing_enabled = settings.getboolean('MCPClient', 'elasticsearch_indexing_enabled', fallback=True)
    if not indexing_enabled:
        print('Skipping indexing because it is currently disabled.')
        return 0

    client = elasticSearchFunctions.connect(settings.get_elasticsearch_hosts())

    print('SIP UUID:', sip_uuid)
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    print('AIP info:', aip_info)
    aip_info = aip_info[0]

    mets_name = 'METS.{}.xml'.format(sip_uuid)
    mets_path = os.path.join(sip_path, mets_name)

    mods_paths = list_mods(sip_path)
    identifiers = []
    for mods in mods_paths:
        identifiers.extend(extract_identifiers_from_mods(mods))

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

    print('Indexing AIP info')
    # Delete ES index before creating new one if reingesting
    if 'REIN' in sip_type:
        elasticSearchFunctions.delete_aip(client, sip_uuid)
        print('Deleted outdated entry for AIP with UUID', sip_uuid, ' from archival storage')

    # Index AIP
    elasticSearchFunctions.index_aip(
        client,
        sip_uuid,
        sip_name,
        aip_info['current_full_path'],
        mets_path,
        size=aip_info['size'],
        aips_in_aic=aips_in_aic,
        identifiers=identifiers)

    # Index AIP files
    print('Indexing AIP files')
    # Even though we treat MODS identifiers as SIP-level, we need to index them
    # here because the archival storage tab actually searches on the
    # aips/aipfile index.
    exitCode = elasticSearchFunctions.index_files(
        client,
        index='aips',
        type='aipfile',
        uuid=sip_uuid,
        pathToArchive=sip_path,
        identifiers=identifiers,
        sipName=sip_name,
    )
    if exitCode == 1:
        print('Error indexing AIP files', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.indexAIP")

    sys.exit(index_aip())
