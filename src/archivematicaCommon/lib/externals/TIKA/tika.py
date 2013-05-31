#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
import os
import sys
import uuid
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from executeOrRunSubProcess import executeOrRun

global runSQLInserts
runSQLInserts = False
global idsDone
idsDone = []

def getTikaID(itemdirectoryPath):
    command = "java -jar ./tika-app-1.3.jar -x -d " + itemdirectoryPath 
    exitCode, stdOut, stdErr = executeOrRun("command", command, printing=False)
    if exitCode == 1: #no id found
        return ""
    if exitCode != 0:
        print >>sys.stderr, "Error: ", stdOut, stdErr, exitCode
        return ""
    return stdOut

def findExtension(itemdirectoryPath):
    basename = os.path.basename(itemdirectoryPath)
    dotI = basename.rfind(".")
    if dotI == -1:
        return ""
    ext = basename[dotI:]
    return ext
    
def findExistingFileID(ext):
    description = 'A %s file' % (ext)
    sql = """SELECT pk, validPreservationFormat, validAccessFormat FROM FileIDs where fileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' AND description = '%s';""" % (description)
    ret = databaseInterface.queryAllSQL(sql)
    if not len(ret):
        return ""
    return ret[0]
    
def printNewCommandRelationships(fileID, fileIDUUID):
    global runSQLInserts
    sql = """SELECT commandClassification, command FROM CommandRelationships WHERE fileID = '%s';""" % (fileID)
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        commandClassification, command = row
        CommandRelationshipUUID = uuid.uuid4().__str__()
        sql = """INSERT INTO CommandRelationships (pk, fileID, commandClassification, command)
            VALUES ('%s', '%s', '%s', '%s');""" % (CommandRelationshipUUID, fileIDUUID, commandClassification, command)
        print sql
        if runSQLInserts:
            databaseInterface.runSQL(sql)



def printTikaInsert(itemdirectoryPath):
    global runSQLInserts
    ext = findExtension(itemdirectoryPath).lower()
    if not ext:
        return
    
    fileID = findExistingFileID(ext)
    if not fileID:
        return
    fileID, validPreservationFormat, validAccessFormat = fileID
    
    tikaFileID = getTikaID(itemdirectoryPath).strip()
    if not tikaFileID:
        return
    
    #check for existing rule
    sql = """SELECT pk FROM FileIDs WHERE fileIDType = '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc' AND description = '%s';""" % tikaFileID 
    if databaseInterface.queryAllSQL(sql):
        a= "skip"
        #return
    if tikaFileID in idsDone:
        return
    
    fileIDUUID = uuid.uuid4().__str__()
    
    sql = """INSERT INTO FileIDs (pk, description, validPreservationFormat, validAccessFormat, fileIDType) 
        VALUES ('%s', '%s', %s, %s, '1d8f3bb3-da8a-4ef6-bac7-b65942df83fc');""" % (fileIDUUID, tikaFileID, validPreservationFormat, validAccessFormat)
    idsDone.append(tikaFileID) 
    print sql
    if runSQLInserts:
        databaseInterface.runSQL(sql)
    
    FileIDsBySingleIDUUID = uuid.uuid4().__str__()
    sql = """INSERT INTO FileIDsBySingleID  (pk, fileID, id, tool, toolVersion)
        VALUES ('%s', '%s', '%s', 'Tika', '1.3');""" % (FileIDsBySingleIDUUID, fileIDUUID, tikaFileID)
    print sql
    
    if runSQLInserts:
        databaseInterface.runSQL(sql)
    
    printNewCommandRelationships(fileID, fileIDUUID)
    
    print
    #print ext, fileID, "\t", tikaFileID.strip()

def goOverFiles(directoryPath):
    directoryContents = os.listdir(directoryPath)
    delayed = []
    for item in directoryContents:
        itemdirectoryPath = os.path.join(directoryPath, item)
        if os.path.isdir(itemdirectoryPath):
            delayed.append(item)

        elif os.path.isfile(itemdirectoryPath):
            printTikaInsert(itemdirectoryPath)
            
    
    for item in sorted(delayed):
        goOverFiles(itemdirectoryPath)


if __name__ == '__main__':
    goOverFiles("./testFiles/")