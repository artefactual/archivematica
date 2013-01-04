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
import sys
import os
import shutil
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
#databaseInterface.printSQL = True

#--sipUUID "%SIPUUID%" --sipDirectory "%SIPDirectory%" --filePath "%relativeLocation%"
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s",  "--sipUUID", action="store", dest="sipUUID", default="")
parser.add_option("-d",  "--sipDirectory", action="store", dest="sipDirectory", default="") #transferDirectory/
parser.add_option("-f",  "--filePath", action="store", dest="filePath", default="") #transferUUID/sipUUID
(opts, args) = parser.parse_args()


filePathLike = opts.filePath.replace(os.path.join(opts.sipDirectory, "objects", "manualNormalization", "access"), "%SIPDirectory%objects", 1)
i = filePathLike.rfind(".")
if i != -1:
     filePathLike = filePathLike[:i+1]
 
filePathLike = databaseInterface.MySQLdb.escape_string(filePathLike).replace("%", "\%") + "%"
unitIdentifierType = "sipUUID"
unitIdentifier = opts.sipUUID
sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation LIKE '" + filePathLike + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
rows = databaseInterface.queryAllSQL(sql)
if len(rows) > 1:
    print >>sys.stderr, "Too many possible files for: ", opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%", 1) 
    exit(2)
elif len(rows) < 1:
    print >>sys.stderr, "No matching file for: ", opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%", 1) 
    exit(3)
for row in rows:
    originalFileUUID, originalFilePath = row

print "matched: {%s}%s" % (originalFileUUID, originalFilePath)
dstFile = originalFileUUID + "-" + os.path.basename(opts.filePath)
dstDir = os.path.join(opts.sipDirectory, "DIP")

try:
    if not os.path.isdir(dstDir):
        os.makedirs(dstDir)
except:
    pass

#Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
#see http://docs.python.org/2/library/os.html
os.rename(opts.filePath, os.path.join(dstDir, dstFile))

exit(0)