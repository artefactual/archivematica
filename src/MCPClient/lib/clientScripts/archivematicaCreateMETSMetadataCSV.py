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

import collections
import csv
import os
import sys
import traceback
# archivematicaCommon
from sharedVariablesAcrossModules import sharedVariablesAcrossModules


def parseMetadata(SIPPath):
    """
    Parse all metadata.csv files in SIPPath.

    Looking for metadata.csvs in metadata/ and
    objects/metadata/transfers/<transfer name>/metadata/

    See parseMetadataCSV for details on parsing.

    :param SIPPath: Path to the SIP
    :return: {<filename>: OrderedDict{<metadata name>=<metadata value>} }
    """
    all_metadata = {}
    # Parse the metadata.csv files from the transfers
    transfersPath = os.path.join(SIPPath, "objects", "metadata", "transfers")
    try:
        transfers = os.listdir(transfersPath)
    except OSError:
        metadata_csvs = []
    else:
        metadata_csvs = [os.path.join(transfersPath, t, "metadata.csv") for t in transfers]

    # Parse the SIP's metadata.csv if it exists
    metadataCSVFilePath = os.path.join(SIPPath, 'objects', 'metadata', 'metadata.csv')
    metadata_csvs.append(metadataCSVFilePath)

    for metadataCSVFilePath in metadata_csvs:
        if os.path.isfile(metadataCSVFilePath):
            try:
                csv_metadata = parseMetadataCSV(metadataCSVFilePath)
            except Exception:
                print >>sys.stderr, "error parsing: ", metadataCSVFilePath
                traceback.print_exc(file=sys.stderr)
                sharedVariablesAcrossModules.globalErrorCount += 1
            # Provide warning if this file already has differing metadata
            # Not using all_metadata.update(csv_metadata) because of that
            for entry, values in csv_metadata.iteritems():
                if entry in all_metadata and all_metadata[entry] != values:
                    print >> sys.stderr, 'Metadata for', entry, 'being updated. Old:', all_metadata[entry], 'New:', values
                existing = all_metadata.get(entry, collections.OrderedDict())
                existing.update(values)
                all_metadata[entry] = existing

    return all_metadata


def parseMetadataCSV(metadataCSVFilePath):
    """
    Parses the metadata.csv into a dict with entries for each file.

    Each file's entry is an OrderedDict containing the column header and value
    for each column.

    Example CSV:
    Filename,dc.title,dc.date,Other metadata
    objects/foo.jpg,Foo,2000,Taken on a sunny day
    objects/bar/,Bar,2000,All taken on a rainy day

    Produces:
    {
        'objects/foo.jpg': OrderedDict(dc.title=Foo, dc.date=2000, Other metadata=Taken on a sunny day)
        'objects/bar': OrderedDict(dc.title=Bar, dc.date=2000, Other metadata=All taken on a rainy day)
    }

    :param metadataCSVFilePath: Path to the metadata CSV to parse
    :return: {<filename>: OrderedDict{<metadata name>=<metadata value>} }
    """
    metadata = {}
    # use universal newline mode to support unusual newlines, like \r
    with open(metadataCSVFilePath, 'rbU') as f:
        reader = csv.reader(f)
        # Parse first row as header
        header = reader.next()
        # Strip filename column, strip whitespace from header values
        header = [h.strip() for h in header[1:]]
        # Parse data
        for row in reader:
            entry_name = row[0]
            if entry_name.endswith("/"):
                entry_name = entry_name[:-1]
            # Strip file/dir name from values
            row = row[1:]
            values = collections.OrderedDict(zip(header, row))
            if entry_name in metadata and metadata[entry_name] != values:
                print >> sys.stderr, 'Metadata for', entry_name, 'being overwritten. Old:', metadata[entry_name], 'New:', values
            metadata[entry_name] = values

    return metadata


if __name__ == '__main__':
    parseMetadata(sys.argv[1])
