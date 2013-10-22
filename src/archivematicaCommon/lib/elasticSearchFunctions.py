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

import ConfigParser
import MySQLdb
import base64
import cPickle
import datetime
import os
import sys
import time
from xml.etree import ElementTree
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import version
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes, xmltodict

pathToElasticSearchServerConfigFile='/etc/elasticsearch/elasticsearch.yml'

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
            'filepath'     : {'type': 'string'},
            'filename'     : {'type': 'string'},
            'fileuuid'     : machine_readable_field_spec,
            'sipuuid'      : machine_readable_field_spec,
            'accessionid'  : machine_readable_field_spec,
            'status'       : machine_readable_field_spec,
            'origin'       : machine_readable_field_spec,
            'ingestdate'   : {'type': 'date' , 'format': 'dateOptionalTime'},
            'created'      : {'type': 'double'}
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
            'FILEUUID': machine_readable_field_spec
        }

        print 'Creating AIP file mapping...'
        conn.put_mapping(
            doc_type='aipfile',
            mapping={'aipfile': {'date_detection': False, 'properties': mapping}},
            indices=['aips']
        )
        print 'AIP file mapping created.'

def connect_and_index_aip(uuid, name, filePath, pathToMETS, size=None):
    conn = connect_and_create_index('aips')

    # convert METS XML to dict
    tree      = ElementTree.parse(pathToMETS)
    root      = tree.getroot()
    xml       = ElementTree.tostring(root)
    mets_data = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

    aipData = {
        'uuid': uuid,
        'name': name,
        'filePath': filePath,
        'size': (size or os.path.getsize(filePath)) / float(1024) / float(1024),
        'mets': mets_data,
        'origin': getDashboardUUID(),
        'created': os.path.getmtime(pathToMETS)
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
            print >>sys.stderr, "Directory does not exist: ", pathToArchive
            exitCode = 1
    else:
        print >>sys.stderr, "Elasticsearch not found, normally installed at ", pathToElasticSearchServerConfigFile
        exitCode = 1

    return exitCode

def index_mets_file_metadata(conn, uuid, metsFilePath, index, type, sipName, backup_to_mysql = False):
    filesIndexed     = 0
    filePathAmdIDs   = {}
    filePathMetsData = {}

    # establish structure to be indexed for each file item
    fileData = {
      'archivematicaVersion': version.get_version(),
      'AIPUUID':   uuid,
      'sipName':   sipName,
      'FILEUUID':  '',
      'indexedAt': time.time(),
      'filePath':  '',
      'fileExtension': '',
      'METS':      {
        'dmdSec': {},
        'amdSec': {}
      },
      'origin': getDashboardUUID()
    }
    dmdSecData = {}

    # parse XML
    tree = ElementTree.parse(metsFilePath)
    root = tree.getroot()

    #before_length = len(ElementTree.tostring(root))

    # add a conditional to toggle this
    # remove FITS output nodes
    fitsOutputNodes = root.findall("{http://www.loc.gov/METS/}amdSec/{http://www.loc.gov/METS/}techMD/{http://www.loc.gov/METS/}mdWrap/{http://www.loc.gov/METS/}xmlData/{info:lc/xmlns/premis-v2}object/{info:lc/xmlns/premis-v2}objectCharacteristics/{info:lc/xmlns/premis-v2}objectCharacteristicsExtension/{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}fits") #/{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}toolOutput")

    for parent in fitsOutputNodes:
        children = parent.findall('{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}toolOutput')
        for node in children:
            parent.remove(node)

    #after_length = len(ElementTree.tostring(root))
    print "Removed FITS output from METS."

    # get SIP-wide dmdSec
    dmdSec = root.findall("{http://www.loc.gov/METS/}dmdSec/{http://www.loc.gov/METS/}mdWrap/{http://www.loc.gov/METS/}xmlData")
    for item in dmdSec:
        xml = ElementTree.tostring(item)
        dmdSecData = xmltodict.parse(xml)

    # get amdSec IDs for each filepath
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp[@USE='original']/{http://www.loc.gov/METS/}file"):
        for item2 in item.findall("{http://www.loc.gov/METS/}FLocat"):
            filePath = item2.attrib['{http://www.w3.org/1999/xlink}href']
            filePathAmdIDs[filePath] = item.attrib['ADMID']

    # for each filepath, get data and convert to dictionary then index everything in the appropriate amdSec element
    for filePath in filePathAmdIDs:
        filesIndexed = filesIndexed + 1
        items = root.findall("{http://www.loc.gov/METS/}amdSec[@ID='" + filePathAmdIDs[filePath] + "']")
        for item in items:
            if item != None:
                xml = ElementTree.tostring(item)

                # set up data for indexing
                indexData = fileData

                indexData['FILEUUID'] = item.find('{http://www.loc.gov/METS/}techMD/{http://www.loc.gov/METS/}mdWrap/{http://www.loc.gov/METS/}xmlData/{info:lc/xmlns/premis-v2}object/{info:lc/xmlns/premis-v2}objectIdentifier/{info:lc/xmlns/premis-v2}objectIdentifierValue').text

                indexData['filePath']   = filePath

                fileName, fileExtension = os.path.splitext(filePath)
                if fileExtension != '':
                    indexData['fileExtension']  = fileExtension[1:].lower()

                indexData['METS']['dmdSec'] = rename_dict_keys_with_child_dicts(normalize_dict_values(dmdSecData))
                indexData['METS']['amdSec'] = rename_dict_keys_with_child_dicts(normalize_dict_values(xmltodict.parse(xml)))

                # index data
                wait_for_cluster_yellow_status(conn)
                result = try_to_index(conn, indexData, index, type)

                if backup_to_mysql:
                    backup_indexed_document(result, indexData, index, type)

    print 'Indexed AIP files and corresponding METS XML.'

    return filesIndexed

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
    filesIndexed = 0
    ingest_date  = str(datetime.datetime.today())[0:10]
    create_time  = time.time()
    # Temporary Archivematica internal files should not be indexed
    exclude_files = ['processingMCP.xml']

    # get accessionId from transfers table using UUID
    accession_id = ''
    sql = "SELECT accessionID from Transfers WHERE transferUUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 0:
        accession_id = rows[0][0]

    for filepath in list_files_in_dir(pathToTransfer):
        if any(f in filepath for f in exclude_files):
            print filepath, 'in excluded files list: skipping'
            continue
        if os.path.isfile(filepath):

            relative_path = '%transferDirectory%objects' + filepath.replace(pathToTransfer, '')

            sql = "SELECT fileUUID FROM Files WHERE currentLocation='" + MySQLdb.escape_string(relative_path) + "' AND transferUUID='" + MySQLdb.escape_string(uuid) + "'"
            rows = databaseInterface.queryAllSQL(sql)
            if len(rows) > 0:
                file_uuid = rows[0][0]
            else:
                file_uuid = ''

            indexData = {
              'filepath'     : filepath,
              'filename'     : os.path.basename(filepath),
              'fileuuid'     : file_uuid,
              'sipuuid'      : uuid,
              'accessionid'  : accession_id,
              'status'       : '',
              'origin'       : getDashboardUUID(),
              'ingestdate'   : ingest_date,
              'created'      : create_time
            }

            _, fileExtension = os.path.splitext(filepath)
            if fileExtension != '':
                indexData['fileExtension']  = fileExtension[1:].lower()

            wait_for_cluster_yellow_status(conn)
            try_to_index(conn, indexData, index, type)

            filesIndexed = filesIndexed + 1

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

def document_id_from_field_query(conn, index, doc_types, field, value):
    document_id = None

    documents = conn.search_raw(
        query=pyes.FieldQuery(pyes.FieldParameter(field, value)),
        doc_types=doc_types
    )

    if len(documents['hits']['hits']) == 1:
        document_id = documents['hits']['hits'][0]['_id']
    return document_id

def connect_and_change_transfer_file_status(uuid, status):
    # TODO: find a way to share this between this script and src/transcoder/lib/transcoderExtraction.py
    SevenZipExtensions = ['.ARJ', '.CAB', '.CHM', '.CPIO',
                  '.DMG', '.HFS', '.LZH', '.LZMA',
                  '.NSIS', '.UDF', '.WIM', '.XAR',
                  '.Z', '.ZIP', '.GZIP', '.TAR',]

    # get file UUIDs for each file in the SIP
    sql = "SELECT fileUUID, currentLocation from Files WHERE transferUUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) > 0:
        conn = connect_and_create_index('transfers')

        # cycle through file UUIDs and update status
        for row in rows:
            is_archive = False

            # the currentLocation may be NULL for archives, which should be ignored
            if row[1] != None:
                for extension in SevenZipExtensions:
                    if row[1].lower().endswith(extension.lower()):
                        is_archive = True

                # archives end up getting expanded into individual files by microservices, so ignore them
                # and ignore certain paths
                ignored_paths = [
                    '%transferDirectory%metadata/manifest-sha512.txt',
                    '%transferDirectory%logs/BagIt/bagit.txt',
                    '%transferDirectory%logs/BagIt/bag-info.txt'
                ]
                if not is_archive and row[1] not in ignored_paths:
                    document_id = document_id_from_field_query(conn, 'transfers', ['transferfile'], 'fileuuid', row[0])

                    if document_id == None:
                        print >>sys.stderr, 'Transfer file ', row[0], ' not found in index.'
                        print 'Transfer file ' + row[0] + ' not found in index.'
                        exit(1)
                    else:
                        conn.update({'status': status}, 'transfers', 'transferfile', document_id)
    return len(rows)

def connect_and_remove_sip_transfer_files(uuid):
    # get file UUIDs for each file in the SIP
    sql = "SELECT fileUUID from Files WHERE sipUUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) > 0:
        conn = connect_and_create_index('transfers')

        # cycle through file UUIDs and delete files from transfer backlog
        for row in rows:
            document_id = document_id_from_field_query(conn, 'transfers', ['transferfile'],  'fileuuid', row[0])
            if document_id != None:
                conn.delete('transfers', 'transferfile', document_id)

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
