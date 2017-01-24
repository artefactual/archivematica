#!/usr/bin/env python2

from __future__ import print_function
import ConfigParser
from glob import glob
import os
import sys

# dashboard
from main.models import UnitVariable

# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions
import storageService as storage_service
import identifier_functions

import django
django.setup()

def get_identifiers(sip_path):
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

    print('Indexing additional identifiers %s', identifiers)

    return identifiers


def index_aip():
    """ Write AIP information to ElasticSearch. """
    sip_uuid = sys.argv[1]  # %SIPUUID%
    sip_name = sys.argv[2]  # %SIPName%
    sip_path = sys.argv[3]  # %SIPDirectory%
    sip_type = sys.argv[4]  # %SIPType%

    # Check if ElasticSearch is enabled
    client_config_path = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(client_config_path)
    elastic_search_disabled = False
    try:
        elastic_search_disabled = config.getboolean(
            'MCPClient', "disableElasticsearchIndexing")
    except ConfigParser.NoOptionError:
        pass
    if elastic_search_disabled:
        print('Skipping indexing: indexing is currently disabled in', client_config_path)
        return 0

    print('SIP UUID:', sip_uuid)
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    print('AIP info:', aip_info)
    aip_info = aip_info[0]

    mets_name = 'METS.{}.xml'.format(sip_uuid)
    mets_path = os.path.join(sip_path, mets_name)

    identifiers = get_identifiers(sip_path)

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
        print('Deleting outdated entry for AIP and AIP files with UUID', sip_uuid, 'from archival storage')
        elasticSearchFunctions.delete_aip(sip_uuid)
        elasticSearchFunctions.connect_and_delete_aip_files(sip_uuid)

    # Index AIP
    elasticSearchFunctions.connect_and_index_aip(
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
    exitCode = elasticSearchFunctions.connect_and_index_files(
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
