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
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from databaseFunctions import escapeForDB
databaseInterface.printSQL = True

a = """SELECT FileIDsBySingleID.fileID, FileIDs.fileIDType, FileIDsBySingleID.id FROM FileIDsBySingleID JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk WHERE FileIDs.fileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' AND FileIDsBySingleID.id = 'raw';"""

def run(target, fileUUID):
    basename = os.path.basename(target)
    extensionIndex = basename.rfind(".")
    if extensionIndex != -1:
        extension = basename[extensionIndex+1:] 
        print "extension:", extension
        sql1= """SELECT FileIDsBySingleID.fileID FROM FileIDsBySingleID JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk WHERE FileIDs.fileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' AND FileIDsBySingleID.id = '%s' AND FileIDs.enabled = TRUE AND FileIDsBySingleID.enabled = TRUE;""" % (escapeForDB(extension.lower())) 
        rows = databaseInterface.queryAllSQL(sql1)  
        for row in rows:
            sql2 = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', '%s');""" % (escapeForDB(fileUUID), row[0])
            databaseInterface.runSQL(sql2)
        
if __name__ == '__main__':
    target = sys.argv[1]
    fileUUID = sys.argv[2]
    run(target, fileUUID)