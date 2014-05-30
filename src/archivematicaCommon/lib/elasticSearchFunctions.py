#!/usr/bin/python -OO

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

import base64
import ConfigParser
import cPickle
import datetime
import logging
import MySQLdb
import os
import re
import sys
import time
from xml.etree import ElementTree

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import version

sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes, xmltodict

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

pathToElasticSearchServerConfigFile='/etc/elasticsearch/elasticsearch.yml'
MAX_QUERY_SIZE = 50000  # TODO Check that this is a reasonable number

def getDashboardUUID():
    sql = "SELECT value FROM DashboardSettings WHERE name='%s'"
    sql = sql % (MySQLdb.escape_string('dashboard_uuid'))

    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) == 1:
        return rows[0][0]

def getElasticsearchServerHostAndPort():
    clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)

    try:
        return config.get('MCPClient', "elasticsearchServer")
    except:
        return '127.0.0.1:9200'

def wait_for_cluster_yellow_status(conn, wait_between_tries=10, max_tries=10):
    health = {}      
    health['status'] = None
    tries = 0       

    # wait for either yellow or green status
    while health['status'] != 'yellow' and health['status'] != 'green' and tries < max_tries:
        tries = tries + 1

        try:
            health = conn.cluster_health()
        except:
            print 'ERROR: failed health check.'
            health['status'] = None

        # sleep if cluster not healthy
        if health['status'] != 'yellow' and health['status'] != 'green':
            print "Cluster not in yellow or green state... waiting to retry."
            time.sleep(wait_between_tries)

def check_server_status_and_create_indexes_if_needed():
    try:
        conn = pyes.ES(getElasticsearchServerHostAndPort())
        conn._send_request('GET', '/')
    except:
        return 'Connection error'

    connect_and_create_index('aips')
    connect_and_create_index('transfers')

    # make sure the mapping for the transfer index types looks OK
    if not transfer_mapping_is_correct(conn):
        return 'The transfer index mapping is incorrect. The "transfers" index should be re-created.'

    # make sure the mapping for the aip index types looks OK
    if not aip_mapping_is_correct(conn):
        return 'The AIP index mapping is incorrect. The "aips" index should be re-created.'

    # no error!
    return 'OK'

def search_raw_wrapper(conn, query, indices=None, doc_types=None, **query_params):
    """
    Performs conn.search_raw with the size set to MAX_QUERY_SIZE.

    By default search_raw returns only 10 results.  Since we usually want all
    results, this is a wrapper that fetches MAX_QUERY_SIZE results and logs a
    warning if more results were available.
    """
    results = conn.search_raw(
        query,
        indices=indices,
        doc_types=doc_types,
        size=MAX_QUERY_SIZE,
        **query_params)

    if results.hits.total > MAX_QUERY_SIZE:
        logging.warning('Number of items in backlog (%s) exceeds maximum amount fetched (%s)', results.hits.total, MAX_QUERY_SIZE)
    return results

def check_server_status():
    try:
        conn = pyes.ES(getElasticsearchServerHostAndPort())
        conn._send_request('GET', '/')
    except:
        return 'Connection error'

    # no errors!
    return 'OK'

def get_type_mapping(conn, index, type):
    return conn._send_request('GET', '/' + index + '/' + type + '/_mapping')

def transfer_mapping_is_correct(conn):
    try:
        # mapping already created
        mapping = get_type_mapping(conn, 'transfers', 'transferfile')
    except:
        # create mapping
        set_up_mapping(conn, 'transfers')
        mapping = get_type_mapping(conn, 'transfers', 'transferfile')

    return mapping['transferfile']['properties']['accessionid']['index'] == 'not_analyzed'

def aip_mapping_is_correct(conn):
    try:
        # mapping already created
        mapping = get_type_mapping(conn, 'aips', 'aipfile')
    except:
        # create mapping
        set_up_mapping(conn, 'aips')
        mapping = get_type_mapping(conn, 'aips', 'aipfile')

    return mapping['aipfile']['properties']['AIPUUID']['index'] == 'not_analyzed'

# try up to three times to get a connection
def connect_and_create_index(index, attempt=1):
    if attempt <= 3:
        conn = pyes.ES(getElasticsearchServerHostAndPort())
        try:
            conn.create_index(index)
            set_up_mapping(conn, index)
            conn = connect_and_create_index(index, attempt + 1)
        except:
            # above exception was pyes.exceptions.IndexAlreadyExistsException
            # but didn't work with ES 0.19.0
            pass
    else:
        conn = False

    return conn

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

def set_up_mapping(conn, index):
    machine_readable_field_spec = {
        'type':  'string',
        'index': 'not_analyzed'
    }

    if index == 'transfers':
        mapping = {
            'filename'     : {'type': 'string'},
            'relative_path': {'type': 'string'},
            'fileuuid'     : machine_readable_field_spec,
            'sipuuid'      : machine_readable_field_spec,
            'accessionid'  : machine_readable_field_spec,
            'status'       : machine_readable_field_spec,
            'origin'       : machine_readable_field_spec,
            'ingestdate'   : {'type': 'date' , 'format': 'dateOptionalTime'},
            'created'      : {'type': 'double'},
            'file_extension': machine_readable_field_spec,
        }

        print 'Creating transfer file mapping...'
        conn.put_mapping(doc_type='transferfile', mapping={'transferfile': {'properties': mapping}}, indices=['transfers'])
        print 'Transfer mapping created.'

    if index == 'aips':
        print 'Creating AIP mapping...'
        conn.put_mapping(doc_type='aip', mapping={'aip': {'date_detection': False}}, indices=['aips'])
        print 'AIP mapping created.'

        mapping = {
            'name': _sortable_string_field_specification('name'),
            'size': {'type': 'double'},
            'uuid': machine_readable_field_spec
        }

        print 'Creating AIP mapping...'
        conn.put_mapping(
            doc_type='aip',
            mapping={'aip': {'date_detection': False, 'properties': mapping}},
            indices=['aips']
        )
        print 'AIP mapping created.'

        mapping = {
            'AIPUUID': machine_readable_field_spec,
            'FILEUUID': machine_readable_field_spec,
            'isPartOf': machine_readable_field_spec,
            'AICID': machine_readable_field_spec,
        }

        print 'Creating AIP file mapping...'
        conn.put_mapping(
            doc_type='aipfile',
            mapping={'aipfile': {'date_detection': False, 'properties': mapping}},
            indices=['aips']
        )
        print 'AIP file mapping created.'

def connect_and_index_aip(uuid, name, filePath, pathToMETS, size=None, aips_in_aic=None):
    conn = connect_and_create_index('aips')

    tree = ElementTree.parse(pathToMETS)
    root = tree.getroot()
    nsmap = { #TODO use XML namespaces from archivematicaXMLNameSpaces.py
        'dc': 'http://purl.org/dc/terms/',
        'm': 'http://www.loc.gov/METS/',
    }
    # Extract AIC identifier, other specially-indexed information
    aic_identifier = None
    is_part_of = None
    dublincore = root.find('m:dmdSec/m:mdWrap/m:xmlData/dc:dublincore', namespaces=nsmap)
    if dublincore is not None:
        aip_type = dublincore.findtext('dc:type', namespaces=nsmap)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext('dc:identifier', namespaces=nsmap)
        is_part_of = dublincore.findtext('dc:isPartOf', namespaces=nsmap)

    # convert METS XML to dict
    xml = ElementTree.tostring(root)
    mets_data = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

    aipData = {
        'uuid': uuid,
        'name': name,
        'filePath': filePath,
        'size': (size or os.path.getsize(filePath)) / float(1024) / float(1024),
        'mets': mets_data,
        'origin': getDashboardUUID(),
        'created': os.path.getmtime(pathToMETS),
        'AICID': aic_identifier,
        'isPartOf': is_part_of,
        'countAIPsinAIC': aips_in_aic,
    }
    wait_for_cluster_yellow_status(conn)
    try_to_index(conn, aipData, 'aips', 'aip')

def try_to_index(conn, data, index, doc_type, wait_between_tries=10, max_tries=10):
    tries = 0

    while tries < max_tries:
        tries = tries + 1

        try:
            return conn.index(data, index, doc_type)
        except:
            print "ERROR: error trying to index."
            time.sleep(wait_between_tries)
            pass
        tries = tries + 1

def connect_and_get_aip_data(uuid):
    conn = connect_and_create_index('aips')
    aips = conn.search(
        query=pyes.FieldQuery(pyes.FieldParameter('uuid', uuid)),
        fields='uuid,name,filePath,size,origin,created'
    )
    return aips[0]

def connect_and_index_files(index, type, uuid, pathToArchive, sipName=None):

    exitCode = 0

    # make sure elasticsearch is installed
    if (os.path.exists(pathToElasticSearchServerConfigFile)):

        clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
        config = ConfigParser.SafeConfigParser()
        config.read(clientConfigFilePath)

        try:
            backup_to_mysql = config.getboolean('MCPClient', "backupElasticSearchDocumentsToMySQL")
        except:
            backup_to_mysql = False

        # make sure transfer files exist
        if (os.path.exists(pathToArchive)):
            conn = connect_and_create_index(index)

            # use METS file if indexing an AIP
            metsFilePath = os.path.join(pathToArchive, 'METS.' + uuid + '.xml')

            # index AIP
            if os.path.isfile(metsFilePath):
                filesIndexed = index_mets_file_metadata(
                    conn,
                    uuid,
                    metsFilePath,
                    index,
                    type,
                    sipName,
                    backup_to_mysql
                )

            # index transfer
            else:
                filesIndexed = index_transfer_files(
                    conn,
                    uuid,
                    pathToArchive,
                    index,
                    type
                )

            print type + ' UUID: ' + uuid
            print 'Files indexed: ' + str(filesIndexed)

        else:
            error_message = "Directory does not exist: " + pathToArchive
            logging.warning(error_message)
            print >>sys.stderr, error_message
            exitCode = 1
    else:
        print >>sys.stderr, "Elasticsearch not found, normally installed at ", pathToElasticSearchServerConfigFile
        exitCode = 1

    return exitCode

def index_mets_file_metadata(conn, uuid, metsFilePath, index, type, sipName, backup_to_mysql = False):

    # parse XML
    tree = ElementTree.parse(metsFilePath)
    root = tree.getroot()
    nsmap = { #TODO use XML namespaces from archivematicaXMLNameSpaces.py
        'dc': 'http://purl.org/dc/terms/',
        'm': 'http://www.loc.gov/METS/',
        'p': 'info:lc/xmlns/premis-v2',
        'f': 'http://hul.harvard.edu/ois/xml/ns/fits/fits_output',
    }

    #before_length = len(ElementTree.tostring(root))

    # add a conditional to toggle this
    # remove FITS output nodes
    fitsOutputNodes = root.findall("m:amdSec/m:techMD/m:mdWrap/m:xmlData/p:object/p:objectCharacteristics/p:objectCharacteristicsExtension/f:fits", namespaces=nsmap) #/f:toolOutput")

    for parent in fitsOutputNodes:
        children = parent.findall('f:toolOutput', namespaces=nsmap)
        for node in children:
            parent.remove(node)

    #after_length = len(ElementTree.tostring(root))
    print "Removed FITS output from METS."

    # get SIP-wide dmdSec
    dmdSec = root.findall("m:dmdSec/m:mdWrap/m:xmlData", namespaces=nsmap)
    dmdSecData = {}
    for item in dmdSec:
        xml = ElementTree.tostring(item)
        dmdSecData = xmltodict.parse(xml)

    # Extract isPartOf (for AIPs) or identifier (for AICs) from DublinCore
    dublincore = root.find('m:dmdSec/m:mdWrap/m:xmlData/dc:dublincore', namespaces=nsmap)
    aic_identifier = None
    is_part_of = None
    if dublincore is not None:
        aip_type = dublincore.findtext('dc:type', namespaces=nsmap)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext('dc:identifier', namespaces=nsmap)
        elif aip_type == "Archival Information Package":
            is_part_of = dublincore.findtext('dc:isPartOf', namespaces=nsmap)

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
        'origin': getDashboardUUID(),
    }

    # Index all files in a fileGrup with USE='original' or USE='metadata'
    original_files = root.findall("m:fileSec/m:fileGrp[@USE='original']/m:file", namespaces=nsmap)
    metadata_files = root.findall("m:fileSec/m:fileGrp[@USE='metadata']/m:file", namespaces=nsmap)
    files = original_files + metadata_files

    # Index AIC METS file if it exists
    for file_ in files:
        indexData = fileData.copy() # Deep copy of dict, not of dict contents

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
            amdSecInfo = root.find("m:amdSec[@ID='{}']".format(admID), namespaces=nsmap)
            fileUUID = amdSecInfo.findtext("m:techMD/m:mdWrap/m:xmlData/p:object/p:objectIdentifier/p:objectIdentifierValue", namespaces=nsmap)

            # Index amdSec information
            xml = ElementTree.tostring(amdSecInfo)
            indexData['METS']['amdSec'] = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

        indexData['FILEUUID'] = fileUUID

        # Get file path from FLocat and extension
        filePath = file_.find('m:FLocat', namespaces=nsmap).attrib['{http://www.w3.org/1999/xlink}href']
        indexData['filePath'] = filePath
        _, fileExtension = os.path.splitext(filePath)
        if fileExtension:
            indexData['fileExtension'] = fileExtension[1:].lower()

        # index data
        wait_for_cluster_yellow_status(conn)
        result = try_to_index(conn, indexData, index, type)

        if backup_to_mysql:
            backup_indexed_document(result, indexData, index, type)

        # Reset fileData['METS']['amdSec'], since it is updated in the loop
        # above. See http://stackoverflow.com/a/3975388 for explanation
        fileData['METS']['amdSec'] = {}

    print 'Indexed AIP files and corresponding METS XML.'

    return len(files)

# To avoid Elasticsearch schema collisions, if a dict value is itself a
# dict then rename the dict key to differentiate it from similar instances
# where the same key has a different value type.
#
def rename_dict_keys_with_child_dicts(data):
    new = {}
    for key in data:
        if type(data[key]) is dict:
            new[key + '_data'] = rename_dict_keys_with_child_dicts(data[key])
        elif type(data[key]) is list:
            new[key + '_list'] = rename_list_elements_if_they_are_dicts(data[key])
        else:
            new[key] = data[key]
    return new

def rename_list_elements_if_they_are_dicts(list):
    for index, value in enumerate(list):
        if type(value) is list:
            list[index] = rename_list_elements_if_they_are_dicts(value)
        elif type(value) is dict:
            list[index] = rename_dict_keys_with_child_dicts(value)
    return list

# Because an XML document node may include one or more children, conversion
# to a dict can result in the converted child being one of two types.
# this causes problems in an Elasticsearch index as it expects consistant
# types to be indexed.
# The below function recurses a dict and if a dict's value is another dict,
# it encases it in a list.
#
def normalize_dict_values(data):
    for key in data:
        if type(data[key]) is dict:
            data[key] = [normalize_dict_values(data[key])]
        elif type(data[key]) is list:
            data[key] = normalize_list_dict_elements(data[key])
    return data

def normalize_list_dict_elements(list):
    for index, value in enumerate(list):
        if type(value) is list:
            list[index] = normalize_list_dict_elements(value)
        elif type(value) is dict:
            list[index] =  normalize_dict_values(value)
    return list

def index_transfer_files(conn, uuid, pathToTransfer, index, type):
    """
    Indexes files in the Transfer with UUID `uuid` at path `pathToTransfer`.

    Returns the number of files indexed.

    conn: ElasticSearch connection - see connect_and_create_index
    uuid: UUID of the Transfer in the DB
    pathToTransfer: path on disk, including the transfer directory and a
        trailing / but not including objects/
    index, type: index and type in ElasticSearch
    """
    filesIndexed = 0
    ingest_date  = str(datetime.datetime.today())[0:10]
    create_time  = time.time()

    # Some files should not be indexed
    # This should match the basename of the file
    ignore_files = [
        'processingMCP.xml',
    ]

    # Get accessionId and name from Transfers table using UUID
    accession_id = ''
    sql = "SELECT accessionID, currentLocation FROM Transfers WHERE transferUUID='{}';".format(MySQLdb.escape_string(uuid))
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 0:
        accession_id = rows[0][0]
        # TODO Transfer name should be stored in the DB, for now parse from path
        transfer_name = rows[0][1].split('/')[-2]

    # Get dashboard UUID
    dashboard_uuid = getDashboardUUID()

    for filepath in list_files_in_dir(pathToTransfer):
        if os.path.isfile(filepath):
            # Get file UUID
            file_uuid = ''
            relative_path = filepath.replace(pathToTransfer, '%transferDirectory%')
            sql = "SELECT fileUUID FROM Files WHERE currentLocation='{}' AND transferUUID='{}';".format(
                MySQLdb.escape_string(relative_path),
                MySQLdb.escape_string(uuid))
            rows = databaseInterface.queryAllSQL(sql)
            if len(rows) > 0:
                file_uuid = rows[0][0]

            # Get file path info
            relative_path = relative_path.replace('%transferDirectory%', transfer_name+'/')
            file_extension = os.path.splitext(filepath)[1][1:].lower()
            filename = os.path.basename(filepath)

            if filename not in ignore_files:
                print 'Indexing {} (UUID: {})'.format(relative_path, file_uuid)

                # TODO Index Backlog Location UUID?
                indexData = {
                  'filename'     : filename,
                  'relative_path' : relative_path,
                  'fileuuid'     : file_uuid,
                  'sipuuid'      : uuid,
                  'accessionid'  : accession_id,
                  'status'       : '',
                  'origin'       : dashboard_uuid,
                  'ingestdate'   : ingest_date,
                  'created'      : create_time,
                  'file_extension': file_extension,
                }

                wait_for_cluster_yellow_status(conn)
                try_to_index(conn, indexData, index, type)

                filesIndexed = filesIndexed + 1
            else:
                print 'Skipping indexing {}'.format(relative_path)

    if filesIndexed > 0:
        conn.refresh()

    return filesIndexed

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

def backup_indexed_document(result, indexData, index, type):
    sql = "INSERT INTO ElasticsearchIndexBackup (docId, data, indexName, typeName) VALUES ('%s', '%s', '%s', '%s')"

    sql = sql % (MySQLdb.escape_string(result['_id']), unicode(base64.encodestring(cPickle.dumps(indexData))), MySQLdb.escape_string(index), MySQLdb.escape_string(type))

    databaseInterface.runSQL(sql)

def _document_ids_from_field_query(conn, index, doc_types, field, value):
    document_ids = []

    # Escape /'s with \\
    searchvalue = value.replace('/', '\\/')
    documents = search_raw_wrapper(
        conn,
        query=pyes.FieldQuery(pyes.FieldParameter(field, searchvalue)),
        doc_types=doc_types
    )

    if len(documents['hits']['hits']) > 0:
        document_ids = [ d['_id'] for d in documents['hits']['hits'] ]

    return document_ids

def connect_and_change_transfer_file_status(uuid, status):
    """ Update all files with sipuuid `uuid` to have status `status`. """
    conn = connect_and_create_index('transfers')
    # Fetch ES info for all files in the SIP
    document_ids = _document_ids_from_field_query(conn, 'transfers', ['transferfile'], 'sipuuid', uuid)
    # Update status
    for doc_id in document_ids:
        conn.update(
            extra_doc={'status': status},
            index='transfers',
            doc_type='transferfile',
            id=doc_id,
        )
    return len(document_ids)


def get_transfer_file_info(field, value):
    """
    Get transferfile information from ElasticSearch with query field = value.
    """
    logging.debug('get_transfer_file_info: field: %s, value: %s', field, value)
    results = {}
    conn = connect_and_create_index('transfers')
    indicies = ['transfers']
    # doc_types='transferfile'
    # Escape /'s with \\
    searchvalue = value.replace('/', '\\/')
    documents = search_raw_wrapper(
        conn,
        pyes.FieldQuery(pyes.FieldParameter(field, searchvalue)),
        indicies=indicies,
    )
    if len(documents['hits']['hits']) > 0:
        results = documents['hits']['hits'][0]['_source']

    logging.debug('get_transfer_file_info: results: %s', results)
    if results.get(field) != value:
        logging.warning('May not be correct transfer info: %s is %s instead of %s', field, results.get(field), value)
    return results


def connect_and_remove_backlog_transfer_files(uuid):
    return connect_and_remove_transfer_files(uuid, 'transfer')

def connect_and_remove_sip_transfer_files(uuid):
    return connect_and_remove_transfer_files(uuid, 'sip')

def connect_and_remove_transfer_files(uuid, unit_type):
    # get file UUIDs for each file in the SIP
    sql = "SELECT fileUUID from Files WHERE " + unit_type + "UUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) > 0:
        conn = connect_and_create_index('transfers')

        # cycle through file UUIDs and delete files from transfer backlog
        for row in rows:
            document_id = _document_ids_from_field_query(conn, 'transfers', ['transferfile'],  'fileuuid', row[0])
            if document_id:
                conn.delete('transfers', 'transferfile', document_id[0])

def delete_aip(uuid):
    return delete_matching_documents('aips', 'aip', 'uuid', uuid)

def delete_matching_documents(index, type, field, value, **kwargs):
    # open connection if one hasn't been provided
    conn = kwargs.get('conn', False)
    if not conn:
        conn = connect_and_create_index(index)

    # a max_documents of 0 means unlimited
    max_documents = kwargs.get('max_documents', 0)

    # cycle through fields to find matches
    documents = conn.search_raw(
        indices=[index],
        doc_types=[type],
        query=pyes.FieldQuery(pyes.FieldParameter(field, value))
    )

    count = 0
    if len(documents['hits']['hits']) > 0:
        for hit in documents['hits']['hits']:
            document_id = hit['_id']
            conn.delete(index, type, document_id)
            count = count + 1
            if count == max_documents:
                return count

    return count

def connect_and_delete_aip_files(uuid):
    deleted = 0
    conn = pyes.ES(getElasticsearchServerHostAndPort())
    documents = conn.search_raw(query=pyes.FieldQuery(pyes.FieldParameter('AIPUUID', uuid)))
    if len(documents['hits']['hits']) > 0:
        for hit in documents['hits']['hits']:
            document_id = hit['_id']
            conn.delete('aips', 'aipfile', document_id)
            deleted = deleted + 1
        print str(deleted) + ' index documents removed.'
    else:
        print 'No AIP files found.'
