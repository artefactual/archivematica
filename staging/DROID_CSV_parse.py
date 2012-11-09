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
# @subpackage transcoder
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import uuid
import sys
import csv
import os
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import traceback
import lxml.etree as etree
from optparse import OptionParser
globalErrorCount = 0

databaseInterface.printSQL = True

csvDirectory = "/home/joseph/PronomIDs/PronomIDs"

tool = 'FITS DROID PUID'


def MAIN():
    global globalErrorCount
    for csvFile in os.listdir(csvDirectory):
        csvFilePath = os.path.join(csvDirectory, csvFile)
        if os.path.isfile(csvFilePath): 
            try:
                with open(csvFilePath, 'rb') as f:
                    reader = csv.reader(f)
                    firstRow = True
                    headerRow = []
                    for row in reader:
                        if firstRow: #header row
                            headerRow = row
                            print headerRow
                            firstRow = False
                        else:
                            insert(csvFile[:-4], row, headerRow)
                    
            except Exception as inst:
                print >>sys.stderr, type(inst)     # the exception instance
                print >>sys.stderr, inst.args
                print >>sys.stderr, "error parsing: ", csvFilePath
                globalErrorCount +=1
                exit(1)

def insert(extension, row, headerRow):
    PUID, FormatName, FormatVersion, FormatRisk, Extension = row
    print extension
    print headerRow
    print row
    
    description = 'PUID="%s", FormatName="%s", FormatVersion="%s", FormatRisk="%s", Extension="%s"' % (PUID, FormatName, FormatVersion, FormatRisk, Extension)
    callWithIDs(PUID, description, extension)
    
    
def callWithIDs(anID, description, extension):
    existingID = alreadyExistsCheck(anID)
    if not existingID:
        print "new id: ", anID
        newIDUUID = uuid.uuid4().__str__()
        newFileID = uuid.uuid4().__str__()
        createNewID(newIDUUID, newFileID, anID, description, extension)
        existingID = newFileID 
    
    else:
        updateWithDescription(existingID, description)
        
    for relationship in findRelationshipsForExtensionIDsForfileUUID(extension):
        createNewReleationshipBasedOn(relationship[0], existingID)

def updateWithDescription(existingID, description):
    sql = """UPDATE FileIDs SET description = '%s' WHERE pk = '%s';""" % (databaseInterface.MySQLdb.escape_string(description), existingID)
    databaseInterface.runSQL(sql)

def createNewReleationshipBasedOn(relationship, existingID):
    #find the command
    sql = "SELECT Command, CommandClassification, GroupMember FROM CommandRelationships WHERE pk = '%s';" % (relationship)
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        Command, Classification, GroupMember = row
        #see if there is already a relationship between this id and the command
        sql = "SELECT PK FROM CommandRelationships WHERE Command = '%s' AND CommandClassification = '%s' AND fileID = '%s';" % (Command, Classification, existingID)
        rows2 = databaseInterface.queryAllSQL(sql)
        if not len(rows2):
            newCommandRelationship = uuid.uuid4().__str__()
            sql = """INSERT INTO CommandRelationships (pk, commandClassification, command, fileID, GroupMember) VALUES ('%s', '%s', '%s', '%s', '%s');""" % (newCommandRelationship, Classification, Command, existingID, GroupMember)
            databaseInterface.runSQL(sql)
        
#
def alreadyExistsCheck(anID):
    #check db for instances of this id
    sql = """SELECT FileID FROM FileIDsBySingleID where id = '%s' AND tool = 'FITS DROID PUID'""" % (anID)
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 1:
        print >>sys.stderr, "Warning. More than one id for %s: %s" % (anID, rows.__str__())
    if len(rows):
        return rows[0][0]
    else:
        return False
    
#
def createNewID(newIDUUID, FileID, anID, description, extension):
    #find the valid preservation/access status
    sql = """SELECT validPreservationFormat, validAccessFormat
                FROM FileIDsBySingleID 
                JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk 
                WHERE FileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' 
                AND FileIDsBySingleID.id = '%s';""" % (extension)
    rows = databaseInterface.queryAllSQL(sql) 
    if len(rows):
        validPreservationFormat, validAccessFormat = rows[0]
    else:
        validPreservationFormat, validAccessFormat = (False, False)
        
    
    fileIDType = 'ac5d97dc-df9e-48b2-81c5-4a8b044355fa'
    sql = """INSERT INTO FileIDs (pk, description, fileIDType, validPreservationFormat, validAccessFormat) VALUES ('%s', '%s', '%s', %s, %s);""" % (FileID, databaseInterface.MySQLdb.escape_string(description), fileIDType, validPreservationFormat, validAccessFormat)
    databaseInterface.runSQL(sql)
    
    sql = """INSERT INTO FileIDsBySingleID (pk, FileID, id, tool) VALUES ('%s', '%s', '%s', 'FITS DROID PUID');""" % (newIDUUID, FileID, anID)
    databaseInterface.runSQL(sql)
    
    
#
def findRelationshipsForExtensionIDsForfileUUID(extension):
    sql = """SELECT CommandRelationships.pk 
                FROM FileIDsBySingleID 
                JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk
                JOIN CommandRelationships ON CommandRelationships.fileID = FileIDs.pk 
                WHERE FileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' 
                AND FileIDsBySingleID.id = '%s';""" % (extension)
    rows = databaseInterface.queryAllSQL(sql)
    return rows    
                
def whatever():
        sql = "SELECT PK FROM CommandRelationships WHERE Command = '%s' AND CommandClassification = '%s' AND fileID = '%s';" % (Command, Classification, existingID)
        rows2 = databaseInterface.queryAllSQL(sql)
        if not len(rows2):
            newCommandRelationship = uuid.uuid4().__str__()
            sql = """INSERT INTO CommandRelationships (pk, commandClassification, command, fileID, GroupMember) VALUES ('%s', '%s', '%s', '%s', '%s');""" % (newCommandRelationship, Classification, Command, existingID, GroupMember)
            databaseInterface.runSQL(sql)
        

if __name__ == '__main__':
    MAIN()
