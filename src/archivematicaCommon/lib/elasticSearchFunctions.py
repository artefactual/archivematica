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

import time, os, sys, MySQLdb, cPickle, base64, ConfigParser, datetime
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes, xmltodict
import xml.etree.ElementTree as ElementTree

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
        mapping = {
            'AIPUUID': machine_readable_field_spec,
            'FILEUUID': machine_readable_field_spec
        }

        print 'Creating AIP file mapping...'
        conn.put_mapping(doc_type='aipfile', mapping={'aipfile': {'properties': mapping}}, indices=['aips'])
        print 'AIP file mapping created.'

def connect_and_index_aip(uuid, name, filePath):
    conn = connect_and_create_index('aips')
    aipData = {
        'uuid':     uuid,
        'name':     name,
        'filePath': filePath,
        'size':     os.path.getsize(filePath) / float(1024) / float(1024),
        'origin':   getDashboardUUID(),
        'created':  time.time()
    }
    conn.index(aipData, 'aips', 'aip')

def connect_and_get_aip_data(uuid):
    conn = connect_and_create_index('aips')
    aips = conn.search(query=pyes.FieldQuery(pyes.FieldParameter('uuid', uuid)))
    return aips[0]

def connect_and_index_files(index, type, uuid, pathToArchive, sipName=None):

    exitCode = 0

    # make sure elasticsearch is installed
    if (os.path.exists(pathToElasticSearchServerConfigFile)):

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
                    sipName
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

def index_mets_file_metadata(conn, uuid, metsFilePath, index, type, sipName):
    filesIndexed     = 0
    filePathAmdIDs   = {}
    filePathMetsData = {}

    # establish structure to be indexed for each file item
    fileData = {
      'archivematicaVersion': '0.9',
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
                result = conn.index(indexData, index, type)

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

    # extract transfer name from path
    path_without_uuid = pathToTransfer[:-45]
    last_slash_position = path_without_uuid.rfind('/')
    transfer_name = path_without_uuid[last_slash_position + 1:]

    # get accessionId from SIPs table using transfer name
    accession_id = ''
    current_path = '%sharedPath%watchedDirectories/system/autoProcessSIP/' + transfer_name + '/'
    sql = "SELECT accessionId from SIPs WHERE currentPath = '" + MySQLdb.escape_string(current_path) + "'"

    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 0:
        accession_id = rows[0][0]

    # get file UUID information
    fileUUIDs = {}
    sql = "SELECT currentLocation, fileUUID FROM Files WHERE transferUUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        file_path = row[0]
        fileUUIDs[file_path] = row[1]

    for filepath in list_files_in_dir(pathToTransfer):
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

            fileName, fileExtension = os.path.splitext(filepath)
            if fileExtension != '':
                indexData['fileExtension']  = fileExtension[1:].lower()

            conn.index(indexData, index, type)

            filesIndexed = filesIndexed + 1

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

def connect_and_change_transfer_file_status(uuid, status):
    # get file UUIDs for each file in the SIP
    sql = "SELECT fileUUID from Files WHERE transferUUID='" + MySQLdb.escape_string(uuid) + "'"

    rows = databaseInterface.queryAllSQL(sql)

    if len(rows) > 0:
        conn = connect_and_create_index('transfers')

        # cycle through file UUIDs and delete files from transfer backlog
        for row in rows:
            documents = conn.search_raw(query=pyes.FieldQuery(pyes.FieldParameter('fileuuid', row[0])))
            if len(documents['hits']['hits']) > 0:
                document_id = documents['hits']['hits'][0]['_id']
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
            documents = conn.search_raw(query=pyes.FieldQuery(pyes.FieldParameter('fileuuid', row[0])))
            if len(documents['hits']['hits']) > 0:
                document_id = documents['hits']['hits'][0]['_id']
                conn.delete('transfers', 'transferfile', document_id)
