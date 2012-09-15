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
# @version svn: $Id$
import sys
import os
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from databaseFunctions import escapeForDB


a = """SELECT * FROM FileExtensions JOIN FileIDsByExtension ON FileExtensions.extension = FileIDsByExtension.Extension JOIN FileIDs ON FileIDsByExtension.FileIDs = FileIDs.pk;"""

def run(target, fileUUID):
    basename = os.path.basename(target)
    extensionIndex = basename.rfind(".")
    if extensionIndex != -1:
        extension = basename[extensionIndex+1:] 
        print "extension:", extension
        sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', (SELECT FileIDs FROM FileIDsByExtension WHERE Extension = '%s'))""" % (escapeForDB(fileUUID), escapeForDB(extension.lower()))
        databaseInterface.runSQL(sql)
        
if __name__ == '__main__':
    target = sys.argv[1]
    fileUUID = sys.argv[2]
    run(target, fileUUID)