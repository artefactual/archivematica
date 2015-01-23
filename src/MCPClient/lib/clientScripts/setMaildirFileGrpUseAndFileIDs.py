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
exitCode = 0
# archivematicaCommon
from externals.extractMaildirAttachments import parse
import databaseInterface


def setArchivematicaMaildirFiles(sipUUID, sipPath):
    for root, dirs, files in os.walk(os.path.join(sipPath, "objects", "attachments")):
        for file in files:
            if file.endswith('.archivematicaMaildir'):
                fileRelativePath = os.path.join(root, file).replace(sipPath, "%SIPDirectory%", 1)
                sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND sipUUID = '%s' AND currentLocation = '%s';""" % (sipUUID, fileRelativePath)
                rows = databaseInterface.queryAllSQL(sql)
                if len(rows):
                    fileUUID = rows[0][0]
                    sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', (SELECT pk FROM FileIDs WHERE enabled = TRUE AND description = 'A .archivematicaMaildir file')); """ % (fileUUID)
                    databaseInterface.runSQL(sql)
        
def setMaildirFiles(sipUUID, sipPath):
    for root, dirs, files in os.walk(os.path.join(sipPath, "objects", "Maildir")):
        for file in files:
            fileRelativePath = os.path.join(root, file).replace(sipPath, "%SIPDirectory%", 1)
            sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND sipUUID = '%s' AND currentLocation = '%s';""" % (sipUUID, fileRelativePath)
            rows = databaseInterface.queryAllSQL(sql)
            if len(rows):
                fileUUID = rows[0][0]
                sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', (SELECT pk FROM FileIDs WHERE enabled = TRUE AND description = 'A maildir email file')); """ % (fileUUID)
                databaseInterface.runSQL(sql)
    
    

if __name__ == '__main__':
    sipUUID = sys.argv[1]
    sipPath = sys.argv[2]
    setMaildirFiles(sipUUID, sipPath)    
    setArchivematicaMaildirFiles(sipUUID, sipPath)
    
    exit(exitCode)