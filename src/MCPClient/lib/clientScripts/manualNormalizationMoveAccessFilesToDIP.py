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
import csv
import os
import shutil
import sys
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

# Search for original file associated with the access file given in filePath
filePathLike = opts.filePath.replace(os.path.join(opts.sipDirectory, "objects", "manualNormalization", "access"), "%SIPDirectory%objects", 1)
i = filePathLike.rfind(".")
if i != -1:
     filePathLike = filePathLike[:i+1]
     # Matches "path/to/file/filename." Includes . so it doesn't false match foobar.txt when we wanted foo.txt
     filePathLike1 = databaseInterface.MySQLdb.escape_string(filePathLike).replace("%", "\%") + "%"
     # Matches the exact filename.  For files with no extension.
     filePathLike2 = databaseInterface.MySQLdb.escape_string(filePathLike)[:-1]
     
unitIdentifierType = "sipUUID"
unitIdentifier = opts.sipUUID
sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation LIKE '" + filePathLike1 + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
rows = databaseInterface.queryAllSQL(sql)
if not len(rows):
    #If not found try without extension
    sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation = '" + filePathLike2 + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
rows = databaseInterface.queryAllSQL(sql)
if len(rows) > 1:
    # There is more than one original file with the same filename (differing extensions)
    # Look for a CSV that will specify the mapping
    csv_path = os.path.join(opts.sipDirectory, "objects", "manualNormalization", 
        "normalization.csv")
    if os.path.isfile(csv_path):
        # Will not work properly if csv_path cannot be opened. (eg permissions)
        # Can we assume that the permissions are OK due to previous chain links?
        with open(csv_path, 'rb') as csv_file:
            reader = csv.reader(csv_file)
            # Search CSV for an access filename that matches the one provided
            access_file = os.path.basename(opts.filePath)
            # Get original name of access file, to handle sanitized names
            # TODO add support for files in subdirectories
            sql = """SELECT Files.originalLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='manualNormalization' AND Files.currentLocation LIKE '%{filename}' AND {unitIdentifierType} = '{unitIdentifier}';""".format(
                filename=access_file, unitIdentifierType=unitIdentifierType, unitIdentifier=unitIdentifier)
            rows = databaseInterface.queryAllSQL(sql)
            if len(rows) != 1:
                print >>sys.stderr, "Access file ({0}) not found in DB.".format(access_file)
                exit(2)
            access_file = os.path.basename(rows[0][0])
            try:
                for row in reader:
                    if "#" in row[0]: # if first character #, ignore line
                        continue
                    original, access, _ = row
                    if access.lower() == access_file.lower():
                        print "Found access file({0}) for original ({1})".format(access, original)
                        break
                else:
                    print >>sys.stderr, "Could not find {access_file} in {filename}".format(
                        access_file=access_file, filename=csv_path)
                    exit(2)
            except csv.Error as e:
                print >>sys.stderr, "Error reading {filename} on line {linenum}".format(
                    filename=csv_path, linenum=reader.line_num)
                exit(2)
        # If we found the original file, retrieve it from the DB
        sql = """SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='original' AND Files.currentLocation LIKE '%{filename}' AND {unitIdentifierType} = '{unitIdentifier}';""".format(
                filename=original, unitIdentifierType=unitIdentifierType, unitIdentifier=unitIdentifier)
        rows = databaseInterface.queryAllSQL(sql)
    else:
        print >>sys.stderr, "Too many possible files for: ", opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%", 1) 
        exit(2)
elif len(rows) < 1:
    print >>sys.stderr, "No matching file for: ", opts.filePath.replace(opts.sipDirectory, "%SIPDirectory%", 1) 
    exit(3)

# We found the original file somewhere above, get the UUID and path
for row in rows:
    originalFileUUID, originalFilePath = row

print "matched: {%s}%s" % (originalFileUUID, originalFilePath)
dstDir = os.path.join(opts.sipDirectory, "DIP", "objects")
dstFile = originalFileUUID + "-" + os.path.basename(opts.filePath)

#ensure unique output file name
i = 0
while os.path.exists(os.path.join(dstDir, dstFile)):
    i+=1
    dstFile = originalFileUUID + "-" + str(i) + "-" + os.path.basename(opts.filePath)
    
try:
    if not os.path.isdir(dstDir):
        os.makedirs(dstDir)
except:
    pass

#Rename the file or directory src to dst. If dst is a directory, OSError will be raised. On Unix, if dst exists and is a file, it will be replaced silently if the user has permission. The operation may fail on some Unix flavors if src and dst are on different filesystems.
#see http://docs.python.org/2/library/os.html
os.rename(opts.filePath, os.path.join(dstDir, dstFile))

exit(0)
