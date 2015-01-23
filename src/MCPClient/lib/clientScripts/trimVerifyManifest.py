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
import re
import os
import sys
import uuid

while False:
    import time
    time.sleep(10)

transferUUID = sys.argv[1]
transferName = sys.argv[2]
transferPath = sys.argv[3]
date = sys.argv[4]
 

# archivematicaCommon
from fileOperations import getFileUUIDLike
import databaseFunctions
topDirectory = None
currentDirectory = ""
fileCount = 0
exitCode = 0



for line in open(os.path.join(transferPath, "manifest.txt"),'r'):
    if line.startswith(" Directory of "):
        if topDirectory == None:
            topDirectory = line.strip()
            currentDirectory = transferPath
            originalTransferName = topDirectory.split('\\')[-1]
            if originalTransferName != transferName:
                print >>sys.stderr, "Warning, transfer was renamed from: ", originalTransferName  
                 
        else:
            currentDirectory = line.strip().replace(topDirectory + '\\', transferPath, 1).replace('\\','/')
  
    #file/dir lines aren't and don't start with whitespace.
    if not line.strip():
        continue
    if line.startswith(" ") or line.startswith("\t"):
        continue
    
    isDir = False
    if line.find('<DIR>') != -1:
        isDir = True
    
    sections = re.split('\s+', line.strip())
    baseName = sections[-1] #assumes no spaces in file name
    path = os.path.join(transferPath, currentDirectory, baseName)
    
    if isDir:
        #don't check if parent directory exists
        if baseName == "..":
            continue
        #check if directory exists
        if os.path.isdir(path):
            print "Verified directory exists: ", path.replace(transferPath, "%TransferDirectory%")
        else:
            print >>sys.stderr, "Directory does not exists: ", path.replace(transferPath, "%TransferDirectory%")
            exitCode += 1
    else:
        if os.path.isfile(path):
            print "Verified file exists: ", path.replace(transferPath, "%TransferDirectory%")
            fileCount += 1
            fileID = getFileUUIDLike(path, transferPath, transferUUID, "transferUUID", "%transferDirectory%")
            if not len(fileID):
                print >>sys.stderr, "Could not find fileUUID for: ", path.replace(transferPath, "%TransferDirectory%")
                exitCode += 1
            for paths, fileUUID in fileID.iteritems():
                eventDetail = "program=\"archivematica\"; module=\"trimVerifyManifest\""
                eventOutcome="Pass"
                eventOutcomeDetailNote = "Verified file exists"
                eventIdentifierUUID=uuid.uuid4().__str__()
                databaseFunctions.insertIntoEvents(fileUUID=fileUUID, \
                     eventIdentifierUUID=eventIdentifierUUID, \
                     eventType="manifest check", \
                     eventDateTime=date, \
                     eventOutcome=eventOutcome, \
                     eventOutcomeDetailNote=eventOutcomeDetailNote, \
                     eventDetail=eventDetail)
        else:
            i = path.rfind(".")
            path2 = path[:i] + path[i:].lower() 
            if i != -1 and os.path.isfile(path2):
                print >>sys.stderr, "Warning, verified file exists, but with implicit extension case: ", path.replace(transferPath, "%TransferDirectory%")
                fileCount += 1
                fileID = getFileUUIDLike(path2, transferPath, transferUUID, "transferUUID", "%transferDirectory%")
                if not len(fileID):
                    print >>sys.stderr, "Could not find fileUUID for: ", path.replace(transferPath, "%TransferDirectory%")
                    exitCode += 1
                for paths, fileUUID in fileID.iteritems():
                    eventDetail = "program=\"archivematica\"; module=\"trimVerifyManifest\""
                    eventOutcome="Pass"
                    eventOutcomeDetailNote = "Verified file exists, but with implicit extension case"
                    eventIdentifierUUID=uuid.uuid4().__str__()
                    databaseFunctions.insertIntoEvents(fileUUID=fileUUID, \
                         eventIdentifierUUID=eventIdentifierUUID, \
                         eventType="manifest check", \
                         eventDateTime=date, \
                         eventOutcome=eventOutcome, \
                         eventOutcomeDetailNote=eventOutcomeDetailNote, \
                         eventDetail=eventDetail)
            else:
                print >>sys.stderr, "File does not exists: ", path.replace(transferPath, "%TransferDirectory%")
                exitCode += 1
if fileCount:
    quit(exitCode)
else:
    print >>sys.stderr, "No files found."
    quit(-1)
