#!/usr/bin/env python2

import os
from lxml import etree as etree
import sys
import uuid

# fileOperations, databaseFunctions requires Django to be set up
import django
django.setup()

# archivematicaCommon
from externals.checksummingTools import get_file_checksum
from fileOperations import getFileUUIDLike
import databaseFunctions

transferUUID = sys.argv[1]
transferName = sys.argv[2]
transferPath = sys.argv[3]
date = sys.argv[4]

currentDirectory = ''
exitCode = 0

for transfer_dir in os.listdir(transferPath):
    dirPath = os.path.join(transferPath, transfer_dir)
    if not os.path.isdir(dirPath):
        continue
    for transfer_file in os.listdir(dirPath):
        filePath = os.path.join(dirPath, transfer_file)
        if transfer_file == 'ContainerMetadata.xml' or transfer_file.endswith('Metadata.xml') or not os.path.isfile(filePath):
            continue

        i = transfer_file.rfind('.')
        if i != -1:
            xmlFile = transfer_file[:i] + '_Metadata.xml'
        else:
            xmlFile = transfer_file + '_Metadata.xml'
        xmlFilePath = os.path.join(dirPath, xmlFile)
        try:
            tree = etree.parse(xmlFilePath)
            root = tree.getroot()

            xmlMD5 = root.find('Document/MD5').text
        except:
            print >>sys.stderr, 'Error parsing: ', xmlFilePath
            exitCode += 1
            continue

        objectMD5 = get_file_checksum(filePath, 'md5')

        if objectMD5 == xmlMD5:
            print 'File OK: ', xmlMD5, filePath.replace(transferPath, '%TransferDirectory%')

            fileID = getFileUUIDLike(filePath, transferPath, transferUUID, 'transferUUID', '%transferDirectory%')
            for path, fileUUID in fileID.iteritems():
                eventDetail = 'program="python"; module="hashlib.md5()"'
                eventOutcome = 'Pass'
                eventOutcomeDetailNote = '%s %s' % (xmlFile.__str__(), 'verified')
                eventIdentifierUUID = uuid.uuid4().__str__()

                databaseFunctions.insertIntoEvents(
                    fileUUID=fileUUID,
                    eventIdentifierUUID=eventIdentifierUUID,
                    eventType='fixity check',
                    eventDateTime=date,
                    eventOutcome=eventOutcome,
                    eventOutcomeDetailNote=eventOutcomeDetailNote,
                    eventDetail=eventDetail
                )
        else:
            print >>sys.stderr, 'Checksum mismatch: ', filePath.replace(transferPath, '%TransferDirectory%')
            exitCode += 1

quit(exitCode)
