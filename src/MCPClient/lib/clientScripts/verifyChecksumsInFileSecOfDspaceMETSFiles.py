#!/usr/bin/python -OO

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
import os
import sys
import lxml.etree as etree
# archivematicaCommon
from externals.checksummingTools import sha_for_file
from externals.checksummingTools import md5_for_file

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory="./"):
    print metsFile
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp/{http://www.loc.gov/METS/}file"):
        #print etree.tostring(item)
        #print item

        checksum = item.get("CHECKSUM")
        checksumType = item.get("CHECKSUMTYPE")
        for item2 in item:
            if item2.tag == "{http://www.loc.gov/METS/}FLocat":
                #print "floc: ", item2.tag, etree.tostring(item2)
                #print item2.attrib
                fileLocation = item2.get("{http://www.w3.org/1999/xlink}href")
        #print "%s - %s - %s " % (checksumType, checksum, fileLocation)
        fileFullPath = os.path.join(relativeDirectory, fileLocation)
        if checksumType == "MD5":
            checksum2 = md5_for_file(fileFullPath)
            eventDetail = "program=\"python\"; module=\"hashlib.sha256()\""
        elif checksumType == "sha256":
            checksum2 = sha_for_file(fileFullPath)
            eventDetail = "program=\"python\"; module=\"hashlib.md5()\""
        else:
            print >>sys.stderr, "Unsupported checksum type: %s" % (checksumType.__str__())
            exit(300)


        if checksum != checksum2:
            #eventOutcomeDetailNote = checksumFile.__str__() + " != " + checksumDB.__str__()
            eventOutcome="Fail"
            print "%s - %s - %s" % ((checksum == checksum2).__str__(), checksum.__str__(), checksum2.__str__())
            print >>sys.stderr, eventOutcome,  fileFullPath
            exitCode = exitCode + 22
        else:
            #eventOutcomeDetailNote = checksumFile.__str__() + "verified"
            eventOutcome="Pass"
            print eventOutcome, fileLocation






    return exitCode


if __name__ == '__main__':
    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]


    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
