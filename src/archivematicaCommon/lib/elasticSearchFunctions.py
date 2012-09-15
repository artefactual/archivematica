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
# @version svn: $Id$

import time
import os
import sys
import MySQLdb
import cPickle
import base64
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
import xmltodict
import xml.etree.ElementTree as ElementTree

pathToElasticSearchServerFile='/etc/elasticsearch/elasticsearch.yml'

def connect_and_index(index, type, uuid, pathToArchive):

    exitCode = 0

    # make sure elasticsearch is installed
    if (os.path.exists(pathToElasticSearchServerFile)):

        # make sure transfer files exist
        if (os.path.exists(pathToArchive)):
            conn = pyes.ES('127.0.0.1:9200')
            try:
                conn.create_index(index)
            except pyes.exceptions.IndexAlreadyExistsException:
                pass

            # use METS file if indexing an AIP
            metsFilePath = os.path.join(pathToArchive, 'METS.' + uuid + '.xml')

            if os.path.isfile(metsFilePath):
                filesIndexed = index_mets_file_metadata(
                    conn,
                    uuid,
                    metsFilePath,
                    index,
                    type
                )

            else:
                filesIndexed = index_directory_files(
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
        print >>sys.stderr, "Elasticsearch not found, normally installed at ", pathToElasticSearchServerFile
        exitCode = 1

    return exitCode

def index_mets_file_metadata(conn, uuid, metsFilePath, index, type):
    filesIndexed     = 0
    filePathAmdIDs   = {}
    filePathMetsData = {}

    # establish structure to be indexed for each file item
    fileData = {
      'archivematicaVersion': '0.9',
      'AIPUUID':   uuid,
      'indexedAt': time.time(),
      'filePath':  '',
      'METS':      {
        'dmdSec': {},
        'amdSec': {}
      }
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
                indexData['filePath'] = filePath
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

def index_directory_files(conn, uuid, pathToTransfer, index, type):
    filesIndexed = 0

    # document structure
    transferData = {
      'uuid': uuid,
      'created': time.time()
    }

    # compile file data (relative filepath, extension, size)
    fileData = {}
    for filepath in list_files_in_dir(pathToTransfer):
        if os.path.isfile(filepath):
            fileData[filepath] = {
              'basename': os.path.basename(filepath)
            }
            filesIndexed = filesIndexed + 1

    transferData['filepaths'] = fileData

    # add document to index
    conn.index(transferData, index, type)

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
