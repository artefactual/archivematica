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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
import re
import os
from lxml import etree as etree
import sys
import traceback
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from externals.checksummingTools import md5_for_file

while False:
    import time
    time.sleep(10)

transferUUID = sys.argv[1]
transferName = sys.argv[2]
transferPath = sys.argv[3]

currentDirectory = ""
exitCode = 0

def callWithException(exception):
    traceback

for dir in os.listdir(transferPath):
    dirPath = os.path.join(transferPath, dir)
    if not os.path.isdir(dirPath):
        continue
    for file in os.listdir(dirPath):
        filePath = os.path.join(dirPath, file)
        if  file == "ContainerMetadata.xml" or file.endswith("Metadata.xml") or not os.path.isfile(filePath):
            continue
        
        i = file.rfind(".")
        xmlFile = file[:i] + "_Metadata.xml"
        xmlFilePath = os.path.join(dirPath, xmlFile) 
        
        tree = etree.parse(xmlFilePath)
        root = tree.getroot()

        extension = root.find("Document/Extension").text
        xmlMD5 = root.find("Document/MD5").text
        
        #if extension.lower() != file[i+1:].lower():
        #    print >>sys.stderr, "Warning, extension mismatch(file/xml): ", file[:i], extension , file[i+1:] 
        
        objectMD5 = md5_for_file(filePath)
        eventDetail = "program=\"python\"; module=\"hashlib.sha256()\""
        
        if objectMD5 == xmlMD5:
            print "File OK: ", xmlMD5, filePath.replace(transferPath, "%TransferDirectory%")
        else:
            print >>sys.stderr, "Checksum mismatch: ", filePath.replace(transferPath, "%TransferDirectory%")
            exitCode += 1
                 
quit(exitCode)
