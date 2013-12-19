# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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

import logging
from main import models
from lxml import etree
from components import helpers
import uuid
from components import helpers
import os, sys, MySQLdb, shutil
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from externals.checksummingTools import sha_for_file
import elasticSearchFunctions, databaseInterface, databaseFunctions
from archivematicaCreateStructuredDirectory import createStructuredDirectory
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

def process_transfer(transfer_uuid):
    # get transfer info
    transfer = models.Transfer.objects.get(uuid=transfer_uuid)
    transfer_path = transfer.currentlocation.replace(
        '%sharedPath%',
        helpers.get_server_config_value('sharedDirectory')
    )

    createStructuredDirectory(transfer_path, createManualNormalizedDirectories=False)

    processingDirectory = helpers.get_server_config_value('processingDirectory')
    transfer_directory_name = os.path.basename(transfer_path[:-1])

    # removed UUID from transfer directory name
    transfer_name = transfer_directory_name[:-37]

    sharedPath = helpers.get_server_config_value('sharedDirectory')

    tmpSIPDir = os.path.join(processingDirectory, transfer_name)
    tmpSIPDir = helpers.pad_destination_filepath_if_it_already_exists(tmpSIPDir)
    tmpSIPDir += "/"
    processSIPDirectory = os.path.join(sharedPath, 'watchedDirectories/SIPCreation/SIPsUnderConstruction') + '/'

    createStructuredDirectory(tmpSIPDir, createManualNormalizedDirectories=False)
    objectsDirectory = os.path.join(transfer_path, 'objects') + '/'

    sipUUID = uuid.uuid4().__str__()
    destSIPDir = os.path.join(processSIPDirectory, transfer_name)
    destSIPDir = helpers.pad_destination_filepath_if_it_already_exists(destSIPDir)
    destSIPDir += "/"
    lookup_path = destSIPDir.replace(sharedPath, '%sharedPath%')
    databaseFunctions.createSIP(lookup_path, sipUUID)

    #move the objects to the SIPDir
    for item in os.listdir(objectsDirectory):
        shutil.move(os.path.join(objectsDirectory, item), os.path.join(tmpSIPDir, "objects", item))

    #get the database list of files in the objects directory
    #for each file, confirm it's in the SIP objects directory, and update the current location/ owning SIP'
    sql = """SELECT  fileUUID, currentLocation FROM Files WHERE removedTime = 0 AND currentLocation LIKE '\%transferDirectory\%objects%' AND transferUUID =  '""" + transfer_uuid + "'"
    for row in databaseInterface.queryAllSQL(sql):
        fileUUID = row[0]
        currentPath = databaseFunctions.deUnicode(row[1])
        currentSIPFilePath = currentPath.replace("%transferDirectory%", tmpSIPDir)
        if os.path.isfile(currentSIPFilePath):
            sql = """UPDATE Files SET currentLocation='%s', sipUUID='%s' WHERE fileUUID='%s'""" % (MySQLdb.escape_string(currentPath.replace("%transferDirectory%", "%SIPDirectory%")), sipUUID, fileUUID)
            databaseInterface.runSQL(sql)
        else:
            print >>sys.stderr, "file not found: ", currentSIPFilePath

    #copy processingMCP.xml file
    src = os.path.join(os.path.dirname(objectsDirectory[:-1]), "processingMCP.xml")
    dst = os.path.join(tmpSIPDir, "processingMCP.xml")
    shutil.copy(src, dst)

    #moveSIPTo processSIPDirectory
    shutil.move(tmpSIPDir, destSIPDir)

    elasticSearchFunctions.connect_and_change_transfer_file_status(transfer_uuid, '')

    # move original files to completed transfers
    completed_directory = os.path.join(sharedPath, 'watchedDirectories/SIPCreation/completedTransfers')
    shutil.move(transfer_path, completed_directory)

    # update DB
    transfer.currentlocation = '%sharedPath%/watchedDirectories/SIPCreation/completedTransfers/' + transfer_name + '-' + transfer_uuid + '/'
    transfer.save()

    return sipUUID

"""
In order to create a SIP from some files that are structured as a completed transfer, but we created manually
(via the SIP arrangement functionality) rather than in the Transfers tab, we have to create an internal
database representation of the transfer. This database representation is referred to during SIP creation.
"""
def initiate_sip_from_files_structured_like_a_completed_transfer(transfer_files_path):
    transfer_uuid = str(uuid.uuid4())

    # replace processing configuration, if any, with default processing configuration
    # and remove pre-selection of pre-normalize file format identification command
    # because this set of files hasn't been actually ran through the transfer phase
    # and therefore isn't identified
    default_processing_config_filepath = helpers.default_processing_config_path()
    processing_config_filepath = os.path.join(transfer_files_path, 'processingMCP.xml')
    shutil.copyfile(default_processing_config_filepath, processing_config_filepath)
    logging.warning('S:' + default_processing_config_filepath)
    logging.warning('D:' + processing_config_filepath)

    if os.path.exists(processing_config_filepath):
        # get processing config XML, if any
        filedata = open(processing_config_filepath, "r")
        elem = etree.parse(filedata)

        root = elem.getroot()
        choices = root.find('preconfiguredChoices')
        for choice in choices:
            if choice.find('appliesTo').text == 'Select pre-normalize file format identification command':
                choices.remove(choice)

        # re-write processing config XML
        filedata = open(processing_config_filepath, "w")
        filedata.write(etree.tostring(root, pretty_print=True))

    # add UUID to path because the backlog's transfer to SIP logic expects it
    transfer_path = transfer_files_path + '-' + transfer_uuid
    shutil.move(transfer_files_path, transfer_path)

    # create transfer DB representation
    transfer = models.Transfer()
    transfer.uuid = transfer_uuid
    transfer.currentlocation = transfer_path + '/'
    transfer.type = 'Standard'
    transfer.save()

    # create file rows for each file in objects directory
    objects_directory = os.path.join(transfer_path, 'objects')
    for dirname, dirnames, filenames in os.walk(objects_directory):
        for filename in filenames:
            filepath = os.path.join(dirname, filename)

            new_file = models.File()
            new_file.uuid = str(uuid.uuid4())
            new_file.transfer = transfer

            # properties that need to be determined using normal path
            new_file.checksum = sha_for_file(filepath).__str__()
            new_file.size = os.path.getsize(filepath).__str__()
            new_file.filegrpuse = 'original'

            # properties that need to be set using abbreviated path
            filepath = filepath.replace(objects_directory, '%transferDirectory%objects')
            new_file.originallocation = filepath
            new_file.currentlocation = filepath
            new_file.save()

    # create ElasticSearch representation of transfer data
    elasticSearchFunctions.connect_and_index_files(
        'transfers',
        'transferfile',
        transfer_uuid,
        os.path.join(transfer_path, 'objects')
    )

    process_transfer(transfer_uuid)
