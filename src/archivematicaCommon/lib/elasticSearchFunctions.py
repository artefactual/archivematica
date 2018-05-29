#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaCommon
# @author Mike Cantelon <mike@artefactual.com>

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import calendar
import datetime
import json
import logging
import os
import re
import sys
import time
from xml.etree import ElementTree

from django.db.models import Q
from main.models import File, Transfer

# archivematicaCommon
from archivematicaFunctions import get_dashboard_uuid
import namespaces as ns
import version

from externals import xmltodict

from elasticsearch import Elasticsearch, ImproperlyConfigured


logger = logging.getLogger('archivematica.common')

MAX_QUERY_SIZE = 50000  # TODO Check that this is a reasonable number
MATCH_ALL_QUERY = {
    "query": {
        "match_all": {}
    }
}
# Returns files which are in the backlog; *omits* files without UUIDs,
# e.g. administrative files (AM metadata and logs directories).
BACKLOG_FILTER_NO_MD_LOGS = {
    'bool': {
        'must': {
            'term': {
                'status': 'backlog',
            },
        },
        'must_not': {
            'term': {
                'fileuuid': '',
            }
        }
    },
}

# Returns files which are in the backlog; *includes* files without UUIDs,
# e.g. administrative files (AM metadata and logs directories).
BACKLOG_FILTER = {
    'bool': {
        'must': {
            'term': {
                'status': 'backlog',
            },
        }
    }
}

MACHINE_READABLE_FIELD_SPEC = {
    'type': 'string',
    'index': 'not_analyzed'
}


class ElasticsearchError(Exception):
    """ Not operational errors. """
    pass


class EmptySearchResultError(ElasticsearchError):
    pass


class TooManyResultsError(ElasticsearchError):
    pass


_es_hosts = None
_es_client = None
DEFAULT_TIMEOUT = 10


def setup(hosts, timeout=DEFAULT_TIMEOUT):
    """
    Initialize Elasticsearch client and share it as the attribute _es_client in
    the current module. An additional attribute _es_hosts is defined containing
    the Elasticsearch hosts (expected types are: string, list or tuple).
    """
    global _es_hosts
    global _es_client

    _es_hosts = hosts
    _es_client = Elasticsearch(**{
        'hosts': _es_hosts,
        'timeout': timeout,
        'dead_timeout': 2
    })


def setup_reading_from_conf(settings):
    setup(settings.ELASTICSEARCH_SERVER, settings.ELASTICSEARCH_TIMEOUT)


def get_host():
    """
    Return one of the Elasticsearch hosts configured in our client. In the
    future this function could look it up in the Elasticsearch client instead
    of using the module attribute _es_hosts, because in an Elasticsearch
    cluster, nodes can be added or removed dynamically.
    """
    if not _es_hosts:
        raise ImproperlyConfigured('The Elasticsearch client has not been set up yet, please call setup() first.')
    if isinstance(_es_hosts, (list, tuple)):
        return _es_hosts[0]
    return _es_hosts


def get_client():
    """
    Obtain the current Elasticsearch client. If undefined, an exception will be
    raised. This function also checks the integrity of the indices expected by
    this application and populate them when they cannot be found.
    """
    if not _es_client:
        raise ImproperlyConfigured('The Elasticsearch client has not been set up yet. Please call setup() first.')
    create_indexes_if_needed(_es_client)  # TODO: find a better place!
    return _es_client


def remove_tool_output_from_mets(doc):
    """
    Given an ElementTree object, removes all objectsCharacteristicsExtensions elements.
    This modifies the existing document in-place; it does not return a new document.

    This helps index METS files, which might otherwise get too large to
    be usable.
    """
    root = doc.getroot()

    # remove tool output nodes
    toolNodes = root.findall("mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension", namespaces=ns.NSMAP)

    for parent in toolNodes:
        parent.clear()

    print("Removed FITS output from METS.")


def wait_for_cluster_yellow_status(client, wait_between_tries=10, max_tries=10):
    health = {}
    health['status'] = None
    tries = 0

    # wait for either yellow or green status
    while health['status'] != 'yellow' and health['status'] != 'green' and tries < max_tries:
        tries = tries + 1

        try:
            health = client.cluster.health()
        except:
            print('ERROR: failed health check.')
            health['status'] = None

        # sleep if cluster not healthy
        if health['status'] != 'yellow' and health['status'] != 'green':
            print("Cluster not in yellow or green state... waiting to retry.")
            time.sleep(wait_between_tries)


def create_indexes_if_needed(client):
    create_aips_index(client)
    create_transfers_index(client)


def create_aips_index(client):
    create_index(client, 'aips')
    if not aip_mapping_is_correct(client):
        raise ElasticsearchError('The AIP index mapping is incorrect. The "aips" index should be re-created.')


def create_transfers_index(client):
    create_index(client, 'transfers')
    if not transfer_mapping_is_correct(client):
        raise ElasticsearchError('The transfer index mapping is incorrect. The "transfers" index should be re-created.')


def search_all_results(client, body, index=None, doc_type=None, **query_params):
    """
    Performs client.search with the size set to MAX_QUERY_SIZE.

    By default search_raw returns only 10 results.  Since we usually want all
    results, this is a wrapper that fetches MAX_QUERY_SIZE results and logs a
    warning if more results were available.
    """
    if isinstance(index, list):
        index = ','.join(index)

    if isinstance(doc_type, list):
        doc_type = ','.join(doc_type)

    results = client.search(
        body=body,
        index=index,
        doc_type=doc_type,
        size=MAX_QUERY_SIZE,
        **query_params)

    if results['hits']['total'] > MAX_QUERY_SIZE:
        logger.warning('Number of items in backlog (%s) exceeds maximum amount fetched (%s)', results['hits']['total'], MAX_QUERY_SIZE)
    return results


def get_type_mapping(client, index, type):
    return client.indices.get_mapping(index, doc_type=type)[index]['mappings']


def transfer_mapping_is_correct(client):
    try:
        # mapping already created
        mapping = get_type_mapping(client, 'transfers', 'transferfile')
    except:  # create mapping
        set_up_mapping(client, 'transfers')
        mapping = get_type_mapping(client, 'transfers', 'transferfile')

    return mapping['transferfile']['properties']['accessionid']['index'] == 'not_analyzed'


def aip_mapping_is_correct(client):
    try:
        # mapping already created
        mapping = get_type_mapping(client, 'aips', 'aipfile')
    except:  # create mapping
        set_up_mapping(client, 'aips')
        mapping = get_type_mapping(client, 'aips', 'aipfile')

    return mapping['aipfile']['properties']['AIPUUID']['index'] == 'not_analyzed'


def create_index(client, index, attempt=1):
    if attempt > 3:
        return
    response = client.indices.create(index, ignore=400)
    if 'error' in response and 'IndexAlreadyExistsException' in response['error']:
        return
    set_up_mapping(client, index)
    create_index(client, index, attempt + 1)


def _sortable_string_field_specification(field_name):
    return {
        'type': 'multi_field',
        'fields': {
            field_name: {'type': 'string'},
            field_name + '_unanalyzed': {
                'type': 'string',
                'index': 'not_analyzed'
            }
        }
    }


def set_up_mapping_aip_index(client):
    # Load external METS mappings
    # These were generated from an AIP which had all the metadata fields filled out,
    # and should represent a pretty complete structure.
    # We don't want to leave this up to dynamic mapping, since automatic type
    # detection may result in some fields being detected as date fields, and
    # subsequently causing problems.
    with open(os.path.normpath(os.path.join(__file__, "..", "elasticsearch", "aip_mets_mapping.json"))) as f:
        aip_mets_mapping = json.load(f)
    with open(os.path.normpath(os.path.join(__file__, "..", "elasticsearch", "aipfile_mets_mapping.json"))) as f:
        aipfile_mets_mapping = json.load(f)

    mapping = {
        'name': _sortable_string_field_specification('name'),
        'size': {'type': 'double'},
        'uuid': MACHINE_READABLE_FIELD_SPEC,
        'mets': aip_mets_mapping,
    }

    logger.info('Creating AIP mapping...')
    client.indices.put_mapping(
        doc_type='aip',
        body={'aip': {'date_detection': False, 'properties': mapping}},
        index='aips'
    )
    logger.info('AIP mapping created.')

    mapping = {
        'AIPUUID': MACHINE_READABLE_FIELD_SPEC,
        'FILEUUID': MACHINE_READABLE_FIELD_SPEC,
        'isPartOf': MACHINE_READABLE_FIELD_SPEC,
        'AICID': MACHINE_READABLE_FIELD_SPEC,
        'sipName': {'type': 'string'},
        'indexedAt': {'type': 'double'},
        'filePath': {'type': 'string'},
        'fileExtension': {'type': 'string'},
        'origin': {'type': 'string'},
        'identifiers': MACHINE_READABLE_FIELD_SPEC,
        'METS': aipfile_mets_mapping,
    }

    logger.info('Creating AIP file mapping...')
    client.indices.put_mapping(
        doc_type='aipfile',
        body={'aipfile': {'date_detection': False, 'properties': mapping}},
        index='aips'
    )
    logger.info('AIP file mapping created.')


def set_up_mapping_transfer_index(client):
    transferfile_mapping = {
        'filename': {'type': 'string'},
        'relative_path': {'type': 'string'},
        'fileuuid': MACHINE_READABLE_FIELD_SPEC,
        'sipuuid': MACHINE_READABLE_FIELD_SPEC,
        'accessionid': MACHINE_READABLE_FIELD_SPEC,
        'status': MACHINE_READABLE_FIELD_SPEC,
        'origin': MACHINE_READABLE_FIELD_SPEC,
        'ingestdate': {'type': 'date', 'format': 'dateOptionalTime'},
        # METS.xml files in transfers sent to backlog will have '' as their
        # modification_date value. This can cause a failure in certain
        # cases---see https://github.com/artefactual/archivematica/issues/719.
        # For this reason, we specify the type and format here and ignore
        # malformed values like ''.
        'modification_date': {'type': 'date', 'format': 'dateOptionalTime',
                              'ignore_malformed': True},
        'created': {'type': 'double'},
        'size': {'type': 'double'},
        'tags': MACHINE_READABLE_FIELD_SPEC,
        'file_extension': MACHINE_READABLE_FIELD_SPEC,
        'bulk_extractor_reports': MACHINE_READABLE_FIELD_SPEC,
        'format': {
            'type': 'nested',
            'properties': {
                'puid': MACHINE_READABLE_FIELD_SPEC,
                'format': {'type': 'string'},
                'group': {'type': 'string'},
            }
        }
    }

    logger.info('Creating transfer file mapping...')
    client.indices.put_mapping(doc_type='transferfile', body={'transferfile': {'properties': transferfile_mapping}},
                               index='transfers')

    logger.info('Transfer file mapping created.')

    transfer_mapping = {
        'name': {'type': 'string'},
        'status': {'type': 'string'},
        'ingest_date': {'type': 'date', 'format': 'dateOptionalTime'},
        'file_count': {'type': 'integer'},
        'uuid': MACHINE_READABLE_FIELD_SPEC,
        'pending_deletion': {'type': 'boolean'}
    }

    logger.info('Creating transfer mapping...')
    client.indices.put_mapping(doc_type='transfer', body={'transfer': {'properties': transfer_mapping}},
                               index='transfers')

    logger.info('Transfer mapping created.')


def set_up_mapping(client, index):
    if index == 'transfers':
        set_up_mapping_transfer_index(client)
    if index == 'aips':
        set_up_mapping_aip_index(client)


def index_aip(client, uuid, name, filePath, pathToMETS, size=None, aips_in_aic=None, identifiers=[], encrypted=False):

    tree = ElementTree.parse(pathToMETS)

    # TODO add a conditional to toggle this
    remove_tool_output_from_mets(tree)

    root = tree.getroot()
    # Extract AIC identifier, other specially-indexed information
    aic_identifier = None
    is_part_of = None
    dublincore = root.find('mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore', namespaces=ns.NSMAP)
    if dublincore is not None:
        aip_type = dublincore.findtext('dc:type', namespaces=ns.NSMAP) or dublincore.findtext('dcterms:type', namespaces=ns.NSMAP)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext('dc:identifier', namespaces=ns.NSMAP) or dublincore.findtext('dcterms:identifier', namespaces=ns.NSMAP)
        is_part_of = dublincore.findtext('dcterms:isPartOf', namespaces=ns.NSMAP)

    # convert METS XML to dict
    xml = ElementTree.tostring(root)
    mets_data = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

    # Pull the create time from the METS header
    mets_hdr = root.find("mets:metsHdr", namespaces=ns.NSMAP)
    mets_created_attr = mets_hdr.get('CREATEDATE')

    created = time.time()

    if mets_created_attr:
        try:
            created = calendar.timegm(time.strptime(mets_created_attr, '%Y-%m-%dT%H:%M:%S'))
        except ValueError:
            print("Failed to parse METS CREATEDATE: %s" % (mets_created_attr))

    aipData = {
        'uuid': uuid,
        'name': name,
        'filePath': filePath,
        'size': (size or os.path.getsize(filePath)) / 1024 / 1024,
        'mets': mets_data,
        'origin': get_dashboard_uuid(),
        'created': created,
        'AICID': aic_identifier,
        'isPartOf': is_part_of,
        'countAIPsinAIC': aips_in_aic,
        'identifiers': identifiers,
        'transferMetadata': _extract_transfer_metadata(root),
        'encrypted': encrypted
    }
    wait_for_cluster_yellow_status(client)
    try_to_index(client, aipData, 'aips', 'aip')


def try_to_index(client, data, index, doc_type, wait_between_tries=10, max_tries=10):
    if max_tries < 1:
        raise ValueError("max_tries must be 1 or greater")
    for _ in xrange(0, max_tries):
        try:
            return client.index(body=data, index=index, doc_type=doc_type)
        except Exception as e:
            print("ERROR: error trying to index.")
            print(e)
            time.sleep(wait_between_tries)

    # If indexing did not succeed after max_tries is already complete,
    # reraise the Elasticsearch exception to aid in debugging.
    raise


def get_aip_data(client, uuid, fields=None):
    search_params = {
        'body': {
            'query': {'term': {'uuid': uuid}}
        },
        'index': 'aips'
    }

    if fields:
        search_params['fields'] = fields

    aips = client.search(**search_params)

    return aips['hits']['hits'][0]


def index_files(client, index, type_, uuid, pathToArchive, identifiers=[], sipName=None, status=''):
    """
    Only used in clientScripts/* and prints to stdout/stderr.
    """
    # Stop if transfer file does not exist
    if not os.path.exists(pathToArchive):
        error_message = "Directory does not exist: " + pathToArchive
        logger.warning(error_message)
        print(error_message, file=sys.stderr)
        return 1

    # Use METS file if indexing an AIP
    metsFilePath = os.path.join(pathToArchive, 'METS.{}.xml'.format(uuid))

    # Index AIP
    if os.path.isfile(metsFilePath):
        files_indexed = index_mets_file_metadata(
            client,
            uuid,
            metsFilePath,
            index,
            type_,
            sipName,
            identifiers=identifiers
        )

    # Index transfer
    else:
        files_indexed = index_transfer_files(
            client,
            uuid,
            pathToArchive,
            index,
            type_,
            status=status
        )

        index_transfer(client, uuid, files_indexed, status=status)

    print(type_ + ' UUID: ' + uuid)
    print('Files indexed: ' + str(files_indexed))
    return 0


def _extract_transfer_metadata(doc):
    return [xmltodict.parse(ElementTree.tostring(el))['transfer_metadata']
            for el in doc.findall("mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/transfer_metadata", namespaces=ns.NSMAP)]


def index_mets_file_metadata(client, uuid, metsFilePath, index, type_, sipName, identifiers=[]):
    # parse XML
    tree = ElementTree.parse(metsFilePath)
    root = tree.getroot()

    # TODO add a conditional to toggle this
    remove_tool_output_from_mets(tree)

    # get SIP-wide dmdSec
    dmdSec = root.findall("mets:dmdSec/mets:mdWrap/mets:xmlData", namespaces=ns.NSMAP)
    dmdSecData = {}
    for item in dmdSec:
        xml = ElementTree.tostring(item)
        dmdSecData = xmltodict.parse(xml)

    # Extract isPartOf (for AIPs) or identifier (for AICs) from DublinCore
    dublincore = root.find('mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore', namespaces=ns.NSMAP)
    aic_identifier = None
    is_part_of = None
    if dublincore is not None:
        aip_type = dublincore.findtext('dc:type', namespaces=ns.NSMAP) or dublincore.findtext('dcterms:type', namespaces=ns.NSMAP)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext('dc:identifier', namespaces=ns.NSMAP) or dublincore.findtext('dcterms:identifier', namespaces=ns.NSMAP)
        elif aip_type == "Archival Information Package":
            is_part_of = dublincore.findtext('dcterms:isPartOf', namespaces=ns.NSMAP)

    # establish structure to be indexed for each file item
    fileData = {
        'archivematicaVersion': version.get_version(),
        'AIPUUID': uuid,
        'sipName': sipName,
        'FILEUUID': '',
        'indexedAt': time.time(),
        'filePath': '',
        'fileExtension': '',
        'isPartOf': is_part_of,
        'AICID': aic_identifier,
        'METS': {
            'dmdSec': rename_dict_keys_with_child_dicts(normalize_dict_values(dmdSecData)),
            'amdSec': {},
        },
        'origin': get_dashboard_uuid(),
        'identifiers': identifiers,
        'transferMetadata': _extract_transfer_metadata(root),
    }

    # Index all files in a fileGrup with USE='original' or USE='metadata'
    original_files = root.findall("mets:fileSec/mets:fileGrp[@USE='original']/mets:file", namespaces=ns.NSMAP)
    metadata_files = root.findall("mets:fileSec/mets:fileGrp[@USE='metadata']/mets:file", namespaces=ns.NSMAP)
    files = original_files + metadata_files

    # Index AIC METS file if it exists
    for file_ in files:
        indexData = fileData.copy()  # Deep copy of dict, not of dict contents

        # Get file UUID.  If and ADMID exists, look in the amdSec for the UUID,
        # otherwise parse it out of the file ID.
        # 'Original' files have ADMIDs, 'Metadata' files don't
        admID = file_.attrib.get('ADMID', None)
        if admID is None:
            # Parse UUID from file ID
            fileUUID = None
            uuix_regex = r'\w{8}-?\w{4}-?\w{4}-?\w{4}-?\w{12}'
            uuids = re.findall(uuix_regex, file_.attrib['ID'])
            # Multiple UUIDs may be returned - if they are all identical, use that
            # UUID, otherwise use None.
            # To determine all UUIDs are identical, use the size of the set
            if len(set(uuids)) == 1:
                fileUUID = uuids[0]
        else:
            amdSecInfo = root.find("mets:amdSec[@ID='{}']".format(admID), namespaces=ns.NSMAP)
            fileUUID = amdSecInfo.findtext("mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectIdentifier/premis:objectIdentifierValue", namespaces=ns.NSMAP)

            # Index amdSec information
            xml = ElementTree.tostring(amdSecInfo)
            indexData['METS']['amdSec'] = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

        indexData['FILEUUID'] = fileUUID

        # Get file path from FLocat and extension
        filePath = file_.find('mets:FLocat', namespaces=ns.NSMAP).attrib['{http://www.w3.org/1999/xlink}href']
        indexData['filePath'] = filePath
        _, fileExtension = os.path.splitext(filePath)
        if fileExtension:
            indexData['fileExtension'] = fileExtension[1:].lower()

        # index data
        wait_for_cluster_yellow_status(client)
        try_to_index(client, indexData, index, type_)

        # Reset fileData['METS']['amdSec'], since it is updated in the loop
        # above. See http://stackoverflow.com/a/3975388 for explanation
        fileData['METS']['amdSec'] = {}

    print('Indexed AIP files and corresponding METS XML.')

    return len(files)


# To avoid Elasticsearch schema collisions, if a dict value is itself a
# dict then rename the dict key to differentiate it from similar instances
# where the same key has a different value type.
def rename_dict_keys_with_child_dicts(data):
    new = {}
    for key in data:
        if isinstance(data[key], dict):
            new[key + '_data'] = rename_dict_keys_with_child_dicts(data[key])
        elif isinstance(data[key], list):
            # Elasticsearch's lists are typed; a list of strings and
            # a list of objects are not the same type. Check the type
            # of the first object in the list and use that as the tag,
            # rather than just tagging this "_list"
            type_of_list = type(data[key][0]).__name__
            new[key + '_' + type_of_list + '_list'] = rename_list_elements_if_they_are_dicts(data[key])
        else:
            new[key] = data[key]
    return new


def rename_list_elements_if_they_are_dicts(data):
    for index, value in enumerate(data):
        if isinstance(value, list):
            data[index] = rename_list_elements_if_they_are_dicts(value)
        elif isinstance(value, dict):
            data[index] = rename_dict_keys_with_child_dicts(value)
    return data


# Because an XML document node may include one or more children, conversion
# to a dict can result in the converted child being one of two types.
# this causes problems in an Elasticsearch index as it expects consistant
# types to be indexed.
# The below function recurses a dict and if a dict's value is another dict,
# it encases it in a list.
def normalize_dict_values(data):
    for key in data:
        if isinstance(data[key], dict):
            data[key] = [normalize_dict_values(data[key])]
        elif isinstance(data[key], list):
            data[key] = normalize_list_dict_elements(data[key])
    return data


def normalize_list_dict_elements(data):
    for index, value in enumerate(data):
        if isinstance(value, list):
            data[index] = normalize_list_dict_elements(value)
        elif isinstance(value, dict):
            data[index] = normalize_dict_values(value)
    return data


def _get_file_formats(f):
    formats = []
    fields = ['format_version__pronom_id',
              'format_version__description',
              'format_version__format__group__description']
    for puid, format, group in f.fileformatversion_set.all().values_list(*fields):
        formats.append({
            'puid': puid,
            'format': format,
            'group': group,
        })

    return formats


def _list_bulk_extractor_reports(transfer_path, file_uuid):
    reports = []
    log_path = os.path.join(transfer_path, 'logs', 'bulk-' + file_uuid)

    if not os.path.isdir(log_path):
        return reports
    for report in ['telephone', 'ccn', 'ccn_track2', 'pii']:
        path = os.path.join(log_path, report + '.txt')
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            reports.append(report)

    return reports


def index_transfer(client, uuid, file_count, status=''):
    """
    Indexes transfer with UUID `uuid`

    :param client: The ElasticSearch client
    :param uuid: The UUID of the transfer we're indexing
    :param file_count: The number of files in this transfer
    :return: None
    """
    try:
        transfer = Transfer.objects.get(uuid=uuid)
        transfer_name = transfer.currentlocation.split('/')[-2]
    except Transfer.DoesNotExist:
        transfer_name = ''

    transfer_data = {
        'name': transfer_name,
        'status': status,
        'ingest_date': str(datetime.datetime.today())[0:10],
        'file_count': file_count,
        'uuid': uuid,
        'pending_deletion': False,
    }

    wait_for_cluster_yellow_status(client)
    try_to_index(client, transfer_data, 'transfers', 'transfer')


def index_transfer_files(client, uuid, pathToTransfer, index, type_, status=''):
    """
    Indexes files in the Transfer with UUID `uuid` at path `pathToTransfer`.

    Returns the number of files indexed.

    client: ElasticSearch client
    uuid: UUID of the Transfer in the DB
    pathToTransfer: path on disk, including the transfer directory and a
        trailing / but not including objects/
    index, type: index and type in ElasticSearch
    """
    files_indexed = 0
    ingest_date = str(datetime.datetime.today())[0:10]

    # Some files should not be indexed
    # This should match the basename of the file
    ignore_files = [
        'processingMCP.xml',
    ]

    # Get accessionId and name from Transfers table using UUID
    try:
        transfer = Transfer.objects.get(uuid=uuid)
        accession_id = transfer.accessionid
        transfer_name = transfer.currentlocation.split('/')[-2]
    except Transfer.DoesNotExist:
        accession_id = transfer_name = ''

    # Get dashboard UUID
    dashboard_uuid = get_dashboard_uuid()

    for filepath in list_files_in_dir(pathToTransfer):
        if os.path.isfile(filepath):
            # Get file UUID
            file_uuid = ''
            modification_date = ''
            relative_path = filepath.replace(pathToTransfer, '%transferDirectory%')
            try:
                f = File.objects.get(currentlocation=relative_path,
                                     transfer_id=uuid)
                file_uuid = f.uuid
                formats = _get_file_formats(f)
                bulk_extractor_reports = _list_bulk_extractor_reports(pathToTransfer, file_uuid)
                if f.modificationtime is not None:
                    modification_date = f.modificationtime.strftime('%Y-%m-%d')
            except File.DoesNotExist:
                file_uuid = ''
                formats = []
                bulk_extractor_reports = []

            # Get file path info
            relative_path = relative_path.replace('%transferDirectory%', transfer_name + '/')
            file_extension = os.path.splitext(filepath)[1][1:].lower()
            filename = os.path.basename(filepath)
            # Size in megabytes
            size = os.path.getsize(filepath) / (1024 * 1024)
            create_time = os.stat(filepath).st_ctime

            if filename not in ignore_files:
                print('Indexing {} (UUID: {})'.format(relative_path, file_uuid))

                # TODO Index Backlog Location UUID?
                indexData = {
                    'filename': filename,
                    'relative_path': relative_path,
                    'fileuuid': file_uuid,
                    'sipuuid': uuid,
                    'accessionid': accession_id,
                    'status': status,
                    'origin': dashboard_uuid,
                    'ingestdate': ingest_date,
                    'created': create_time,
                    'modification_date': modification_date,
                    'size': size,
                    'tags': [],
                    'file_extension': file_extension,
                    'bulk_extractor_reports': bulk_extractor_reports,
                    'format': formats,
                }

                wait_for_cluster_yellow_status(client)
                try_to_index(client, indexData, index, type_)

                files_indexed = files_indexed + 1
            else:
                print('Skipping indexing {}'.format(relative_path))

    if files_indexed > 0:
        client.indices.refresh()

    return files_indexed


def list_files_in_dir(path, filepaths=[]):
    # define entries
    for file in os.listdir(path):
        child_path = os.path.join(path, file)
        filepaths.append(child_path)

        # if entry is a directory, recurse
        if os.path.isdir(child_path) and os.access(child_path, os.R_OK):
            list_files_in_dir(child_path, filepaths)

    # return fully traversed data
    return filepaths


def _document_ids_from_field_query(client, index, doc_types, field, value):
    document_ids = []

    # Escape /'s with \\
    searchvalue = value.replace('/', '\\/')
    query = {
        'query': {
            'term': {
                field: searchvalue
            }
        }
    }
    documents = search_all_results(
        client,
        body=query,
        doc_type=doc_types
    )

    if len(documents['hits']['hits']) > 0:
        document_ids = [d['_id'] for d in documents['hits']['hits']]

    return document_ids


def document_id_from_field_query(client, index, doc_types, field, value):
    document_id = None
    query = {
        "query": {
            "term": {
                field: value
            }
        }
    }
    documents = search_all_results(
        client,
        body=query,
        doc_type=doc_types
    )
    if len(documents['hits']['hits']) == 1:
        document_id = documents['hits']['hits'][0]['_id']
    return document_id


def get_file_tags(client, uuid):
    """
    Retrieve the complete set of tags for the file with the fileuuid `uuid`.
    Returns a list of zero or more strings.

    :param Elasticsearch client: Elasticsearch client
    :param str uuid: A file UUID.
    """
    query = {
        'query': {
            "term": {
                "fileuuid": uuid,
            }
        }
    }

    results = client.search(
        body=query,
        index='transfers',
        doc_type='transferfile',
        fields='tags',
    )

    count = results['hits']['total']
    if count == 0:
        raise EmptySearchResultError('No matches found for file with UUID {}'.format(uuid))
    if count > 1:
        raise TooManyResultsError('{} matches found for file with UUID {}; unable to fetch a single result'.format(count, uuid))

    result = results['hits']['hits'][0]
    if 'fields' not in result:  # file has no tags
        return []
    return result['fields']['tags']


def set_file_tags(client, uuid, tags):
    """
    Updates the file(s) with the fileuuid `uuid` to the provided value(s).

    :param Elasticsearch client: Elasticsearch client
    :param str uuid: A file UUID.
    :param list tags: A list of zero or more tags.
        Passing an empty list clears the file's tags.
    """
    document_ids = _document_ids_from_field_query(client, 'transfers', ['transferfile'], 'fileuuid', uuid)

    count = len(document_ids)
    if count == 0:
        raise EmptySearchResultError('No matches found for file with UUID {}'.format(uuid))
    if count > 1:
        raise TooManyResultsError('{} matches found for file with UUID {}; unable to fetch a single result'.format(count, uuid))

    doc = {
        'doc': {
            'tags': tags,
        }
    }
    client.update(
        body=doc,
        index='transfers',
        doc_type='transferfile',
        id=document_ids[0]
    )
    return True


def get_transfer_file_info(client, field, value):
    """
    Get transferfile information from ElasticSearch with query field = value.
    """
    logger.debug('get_transfer_file_info: field: %s, value: %s', field, value)
    results = {}
    indicies = 'transfers'
    query = {
        "query": {
            "term": {
                field: value
            }
        }
    }
    documents = search_all_results(client, body=query, index=indicies)
    result_count = len(documents['hits']['hits'])
    if result_count == 1:
        results = documents['hits']['hits'][0]['_source']
    elif result_count > 1:
        # Elasticsearch was sometimes ranking results for a different filename above
        # the actual file being queried for; in that case only consider results
        # where the value is an actual precise match.
        filtered_results = [results for results in documents['hits']['hits']
                            if results['_source'][field] == value]

        result_count = len(filtered_results)
        if result_count == 1:
            results = filtered_results[0]['_source']
        if result_count > 1:
            results = filtered_results[0]['_source']
            logger.warning('get_transfer_file_info returned %s results for query %s: %s (using first result)',
                           result_count, field, value)
        elif result_count < 1:
            logger.error('get_transfer_file_info returned no exact results for query %s: %s',
                         field, value)
            raise ElasticsearchError("get_transfer_file_info returned no exact results")

    logger.debug('get_transfer_file_info: results: %s', results)
    return results


def remove_backlog_transfer(client, uuid):
    return delete_matching_documents(client, 'transfers', 'transfer', 'uuid', uuid)


def remove_backlog_transfer_files(client, uuid):
    return remove_transfer_files(client, uuid, 'transfer')


def remove_sip_transfer_files(client, uuid):
    return remove_transfer_files(client, uuid, 'sip')


def remove_transfer_files(client, uuid, unit_type=None):
    if unit_type == 'transfer':
        transfers = {uuid}
    else:
        condition = Q(transfer_id=uuid) | Q(sip_id=uuid)
        transfers = {f[0] for f in File.objects.filter(condition).values_list('transfer_id')}

    if len(transfers) > 0:
        for transfer in transfers:
            files = _document_ids_from_field_query(client, 'transfers', ['transferfile'], 'sipuuid', transfer)
            if len(files) > 0:
                for f in files:
                    client.delete('transfers', 'transferfile', f)
    else:
        if not unit_type:
            unit_type = 'transfer or SIP'
        logger.warning("No transfers found for %s %s", unit_type, uuid)


def delete_aip(client, uuid):
    return delete_matching_documents(client, 'aips', 'aip', 'uuid', uuid)


def delete_aip_files(client, uuid):
    return delete_matching_documents(client, 'aips', 'aipfile', 'AIPUUID', uuid)


def delete_matching_documents(client, index, doc_type, field, value):
    """
    Deletes all documents in index & doc_type where field = value

    :param Elasticsearch client: Elasticsearch client
    :param str index: Name of the index. E.g. 'aips'
    :param str doc_type: Document type in the index. E.g. 'aip'
    :param str field: Field to query when deleting. E.g. 'uuid'
    :param str value: Value of the field to query when deleting. E.g. 'cd0bb626-cf27-4ca3-8a77-f14496b66f04'
    :return: True if succeeded on shards, false otherwise
    """
    query = {
        "query": {
            "term": {
                field: value
            }
        }
    }
    logger.info('Deleting with query %s', query)
    results = client.delete_by_query(
        index=index,
        doc_type=doc_type,
        body=query
    )

    logger.info('Deleted by query %s', results)

    return results['_indices'][index]['_shards']['successful'] == results['_indices'][index]['_shards']['total']


def update_field(client, uuid, index, doc_type, field, status):
    document_id = document_id_from_field_query(client, index, [doc_type], 'uuid', uuid)

    if document_id is None:
        logger.error('Unable to find document with UUID {} in index {}'.format(uuid, index))
        return

    client.update(
        body={
            'doc': {
                field: status
            }
        },
        index=index,
        doc_type=doc_type,
        id=document_id
    )


def mark_aip_deletion_requested(client, uuid):
    update_field(client, uuid, 'aips', 'aip', 'status', 'DEL_REQ')


def mark_aip_stored(client, uuid):
    update_field(client, uuid, 'aips', 'aip', 'status', 'UPLOADED')


def mark_backlog_deletion_requested(client, uuid):
    update_field(client, uuid, 'transfers', 'transfer', 'pending_deletion', True)


def normalize_results_dict(d):
    """
    Given an ElasticSearch response, returns a normalized copy of its fields dict.

    The "fields" dict always returns all sections of the response as arrays; however, for Archivematica's records, only a single value is ever contained.
    This normalizes the dict by replacing the arrays with their first value.
    """
    return {k: v[0] for k, v in d['fields'].items()}


def augment_raw_search_results(raw_results):
    """
    This function takes JSON returned by an ES query and returns the source document for each result.

    :param raw_results: the raw JSON result from an elastic search query
    :return: JSON result simplified, with document_id set
    """
    modifiedResults = []

    for item in raw_results['hits']['hits']:
        clone = item['_source'].copy()
        clone['document_id'] = item[u'_id']
        modifiedResults.append(clone)

    return modifiedResults
