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
import sys
import os
import shutil
import uuid
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoDerivations
#databaseInterface.printSQL = True
while False:
    import time
    time.sleep(10)

#"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%fileUUID%" "%filePath%"
SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]
fileUUID = sys.argv[4]
filePath = sys.argv[5]
date = sys.argv[6]

filePathLike = filePath.replace(os.path.join(SIPDirectory, "objects", "manualNormalization", "preservation"), "%SIPDirectory%objects", 1)
i = filePathLike.rfind(".")
k = os.path.basename(filePath).rfind(".")
if i != -1 and k != -1:
     filePathLike = filePathLike[:i+1]
     filePathLike1 = databaseInterface.MySQLdb.escape_string(filePathLike).replace("%", "\%") + "%"
     filePathLike2 = databaseInterface.MySQLdb.escape_string(filePathLike)[:-1]
unitIdentifierType = "sipUUID"
unitIdentifier = SIPUUID
sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation LIKE '" + filePathLike1 + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
rows = databaseInterface.queryAllSQL(sql)
if not len(rows):
    sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation LIKE '" + filePathLike2 + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
    rows = databaseInterface.queryAllSQL(sql)
if len(rows) > 1:
    print >>sys.stderr, "Too many possible files for: ", filePath.replace(SIPDirectory, "%SIPDirectory%", 1) 
    exit(2)
elif len(rows) < 1:
    print >>sys.stderr, "No matching file for: ", filePath.replace(SIPDirectory, "%SIPDirectory%", 1) 
    exit(3)
for row in rows:
    originalFileUUID, originalFilePath = row

print "matched: {%s}%s" % (originalFileUUID, originalFilePath)
basename = os.path.basename(filePath)
i = basename.rfind(".")
dstFile = basename[:i] + "-" + fileUUID + basename[i:] 
dstDir = os.path.dirname(originalFilePath.replace("%SIPDirectory%", SIPDirectory, 1))
dst = os.path.join(dstDir, dstFile)
dstR = dst.replace(SIPDirectory, "%SIPDirectory%", 1)

if os.path.isfile(dst) or os.path.isdir(dst):
    print >>sys.stderr, "already exists:", dstR
    exit(2)
    
#Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
#see http://docs.python.org/2/library/os.html
os.rename(filePath, dst)
sql =  """UPDATE Files SET currentLocation='%s' WHERE fileUUID='%s';""" % (dstR, fileUUID)
databaseInterface.runSQL(sql)

derivationEventUUID = uuid.uuid4().__str__()
insertIntoEvents(fileUUID=originalFileUUID, \
               eventIdentifierUUID=derivationEventUUID, \
               eventType="normalization", \
               eventDateTime=date, \
               eventDetail="manual normalization", \
               eventOutcome="", \
               eventOutcomeDetailNote=dstR)

#Add linking information between files
insertIntoDerivations(sourceFileUUID=originalFileUUID, derivedFileUUID=fileUUID, relatedEventUUID=derivationEventUUID)


exit(0)