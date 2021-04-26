#!/usr/bin/env python2
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

# /src/dashboard/src/main/models.py

import collections
import csv
import sys
import traceback

# archivematicaCommon
import archivematicaFunctions
from six.moves import zip


def parseMetadata(job, SIPPath, state):
    """
    Parse all metadata.csv files in SIPPath.

    Looking for metadata.csvs in metadata/ and
    objects/metadata/transfers/<transfer name>/metadata/

    See parseMetadataCSV for details on parsing.

    :param SIPPath: Path to the SIP
    :return: {<filename>: OrderedDict(key: [values]) }
    """
    all_metadata = {}
    metadata_csvs = archivematicaFunctions.find_metadata_files(SIPPath, "metadata.csv")

    for metadataCSVFilePath in metadata_csvs:
        try:
            csv_metadata = parseMetadataCSV(job, metadataCSVFilePath)
        except Exception:
            job.pyprint("error parsing: ", metadataCSVFilePath, file=sys.stderr)
            job.print_error(traceback.format_exc())
            state.error_accumulator.error_count += 1
            continue
        # Provide warning if this file already has differing metadata
        # Not using all_metadata.update(csv_metadata) because of that
        for entry, values in csv_metadata.items():
            if entry in all_metadata and all_metadata[entry] != values:
                job.pyprint(
                    "Metadata for",
                    entry,
                    "being updated. Old:",
                    all_metadata[entry],
                    "New:",
                    values,
                    file=sys.stderr,
                )
            existing = all_metadata.get(entry, collections.OrderedDict())
            existing.update(values)
            all_metadata[entry] = existing

    return all_metadata


def parseMetadataCSV(job, metadataCSVFilePath):
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
    with open(metadataCSVFilePath, "rU") as f:
        reader = csv.reader(f)
        # Parse first row as header
        header = next(reader)
        # Strip filename column, strip whitespace from header values
        header = [h.strip() for h in header[1:]]
        # Parse data
        for row in reader:
            if not row:
                continue
            entry_name = row[0]
            if entry_name.endswith("/"):
                entry_name = entry_name[:-1]
            # Strip file/dir name from values
            row = row[1:]
            values = archivematicaFunctions.OrderedListsDict(list(zip(header, row)))
            if entry_name in metadata and metadata[entry_name] != values:
                job.pyprint(
                    "Metadata for",
                    entry_name,
                    "being overwritten. Old:",
                    metadata[entry_name],
                    "New:",
                    values,
                    file=sys.stderr,
                )
            metadata[entry_name] = values

    return collections.OrderedDict(metadata)  # Return a normal OrderedDict
