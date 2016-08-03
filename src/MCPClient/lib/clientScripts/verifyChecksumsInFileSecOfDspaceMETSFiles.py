#!/usr/bin/env python2

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

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import print_function
import hashlib
import os
import sys
import lxml.etree as etree

from archivematicaFunctions import get_file_checksum

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory="./"):
    print(metsFile)
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp/{http://www.loc.gov/METS/}file"):
        checksum = item.get("CHECKSUM")
        checksumType = item.get('CHECKSUMTYPE', '').lower()

        for item2 in item:
            if item2.tag == "{http://www.loc.gov/METS/}FLocat":
                fileLocation = item2.get("{http://www.w3.org/1999/xlink}href")

        fileFullPath = os.path.join(relativeDirectory, fileLocation)

        if checksumType and checksumType in hashlib.algorithms:
            checksum2 = get_file_checksum(fileFullPath, checksumType)
            eventDetail = 'program="python"; module="hashlib.{}()"'.format(checksumType)
        else:
            print("Unsupported checksum type: %s" % (checksumType.__str__()), file=sys.stderr)
            exit(300)

        if checksum != checksum2:
            eventOutcome = "Fail"
            print("%s - %s - %s" % ((checksum == checksum2).__str__(), checksum.__str__(), checksum2.__str__()))
            print(eventOutcome, fileFullPath, file=sys.stderr)
            exitCode = exitCode + 22
        else:
            eventOutcome = "Pass"
            print(eventOutcome, fileLocation)

    return exitCode


if __name__ == '__main__':
    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]

    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
