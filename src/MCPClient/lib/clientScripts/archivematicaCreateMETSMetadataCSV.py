#!/usr/bin/env python2

import collections
import csv
import os
import sys
import traceback
# archivematicaCommon
import archivematicaFunctions
from custom_handlers import get_script_logger
from sharedVariablesAcrossModules import sharedVariablesAcrossModules


def parseMetadata(SIPPath):
    """
    Parse all metadata.csv files in SIPPath.

    Looking for metadata.csvs in metadata/ and
    objects/metadata/transfers/<transfer name>/metadata/

    See parseMetadataCSV for details on parsing.

    :param SIPPath: Path to the SIP
    :return: {<filename>: OrderedDict(key: [values]) }
    """
    all_metadata = {}
    metadata_csvs = archivematicaFunctions.find_metadata_files(SIPPath, 'metadata.csv')

    for metadataCSVFilePath in metadata_csvs:
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

    Each file's entry is an OrderedDict containing the column header and a list of values for each column.

    Example CSV:
    Filename,dc.title,dc.type,dc.type,Other metadata
    objects/foo.jpg,Foo,Photograph,Still Image,Taken on a sunny day
    objects/bar/,Bar,Photograph,Still Image,All taken on a rainy day

    Produces:
    {
        'objects/foo.jpg': OrderedDict(dc.title=[Foo], dc.type=[Photograph, Still Image], Other metadata=[Taken on a sunny day])
        'objects/bar': OrderedDict(dc.title=[Bar], dc.date=[Photograph, Still Image], Other metadata=[All taken on a rainy day])
    }

    :param metadataCSVFilePath: Path to the metadata CSV to parse
    :return: {<filename>: OrderedDict(<metadata name>: [<metadata value>]) }
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
            values = archivematicaFunctions.OrderedListsDict(zip(header, row))
            if entry_name in metadata and metadata[entry_name] != values:
                print >> sys.stderr, 'Metadata for', entry_name, 'being overwritten. Old:', metadata[entry_name], 'New:', values
            metadata[entry_name] = values

    return collections.OrderedDict(metadata)  # Return a normal OrderedDict


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.createMETSMetadataCSV")

    parseMetadata(sys.argv[1])
