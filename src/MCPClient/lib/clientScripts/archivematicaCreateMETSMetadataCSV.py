#!/usr/bin/python -OO
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#/src/dashboard/src/main/models.py


import os
import sys
import csv
import traceback
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from sharedVariablesAcrossModules import sharedVariablesAcrossModules

METADATA_CSV_KEY = []
METADATA_CSV_VALUE = {}

CSVMetadata = (METADATA_CSV_KEY, METADATA_CSV_VALUE)


def parseMetadata(SIPPath):
    # Parse the metadata.csv files from the transfers
    transfersPath = os.path.join(SIPPath, "objects", "metadata", "transfers")
    try:
        transfers = os.listdir(transfersPath)
    except OSError:
        transfers = []

    for transfer in transfers:
        metadataCSVFilePath = os.path.join(transfersPath,
                                           transfer, "metadata.csv")
        if os.path.isfile(metadataCSVFilePath):
            try:
                parseMetadataCSV(metadataCSVFilePath)
            except Exception:
                print >>sys.stderr, "error parsing: ", metadataCSVFilePath
                traceback.print_exc(file=sys.stderr)
                sharedVariablesAcrossModules.globalErrorCount += 1
    # Parse the SIP's metadata.csv if it exists
    metadataCSVFilePath = os.path.join(SIPPath, 'objects', 'metadata', 'metadata.csv')
    if os.path.isfile(metadataCSVFilePath):
        try:
            parseMetadataCSV(metadataCSVFilePath)
        except Exception:
            print >>sys.stderr, "error parsing: ", metadataCSVFilePath
            traceback.print_exc(file=sys.stderr)
            sharedVariablesAcrossModules.globalErrorCount += 1


def parseMetadataCSV(metadataCSVFilePath):
    # use universal newline mode to support unusual newlines, like \r
    with open(metadataCSVFilePath, 'rbU') as f:
        reader = csv.reader(f)
        # Parse first row as header
        # TODO? Check that header is either Parts or Filename?
        row = reader.next()
        METADATA_CSV_KEY.extend(row)
        # Parse data
        for row in reader:
            entry_name = row[0]
            if METADATA_CSV_VALUE.get(entry_name) and METADATA_CSV_VALUE[entry_name] != row:
                print >> sys.stderr, 'Metadata for', entry_name, 'being overwritten. Old:', METADATA_CSV_VALUE[entry_name], 'New:', row
            if entry_name.endswith("/"):
                entry_name = entry_name[:-1]
            METADATA_CSV_VALUE[entry_name] = row
    global CSVMetadata
    return CSVMetadata


if __name__ == '__main__':
    parseMetadata(sys.argv[1])
