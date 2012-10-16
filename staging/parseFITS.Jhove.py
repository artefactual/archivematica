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
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import traceback
import lxml.etree as etree
from optparse import OptionParser

databaseInterface.printSQL = False

def identifyFromFileUUID(fileUUID, callWithIDs):
    #get the fits text from the database
    for FITSText in databaseInterface.queryAllSQL("SELECT FITSxml FROM FilesFits WHERE fileUUID = '%s'" % (fileUUID)):
        identifyFromFitsText(FITSText[0], fileUUID, callWithIDs)

def identifyFromFitsText(FITSText, fileUUID, callWithIDs):
    #turn text into extree xml
    parser = etree.XMLParser(remove_blank_text=True)
    FITS_XML = etree.XML(FITSText, parser)
    identifyFromXMLObjects(FITS_XML, fileUUID, callWithIDs)
    

def identifyFromXMLObjects(FITS_XML, fileUUID, callWithIDs):
    #parse out the actual file IDs
    #print type(FITS_XML)
    #print etree.tostring(FITS_XML, pretty_print = True)
    for element in FITS_XML.getiterator("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}tool"):
        if element.get("name") == "Jhove":
            for element2 in element.getiterator("{}format"):
                if element2.text != None:
                    callWithIDs(element2.text, fileUUID)
    

def callWithIDs(anID, fileUUID):
    existingID = alreadyExistsCheck(anID)
    if not existingID:
        print "new id: ", anID
        newIDUUID = uuid.uuid4().__str__()
        newFileID = uuid.uuid4().__str__()
        createNewID(newIDUUID, newFileID, anID, fileUUID)
        existingID = newFileID 
    
        
    for relationship in findRelationshipsForExtensionIDsForfileUUID(fileUUID):
        createNewReleationshipBasedOn(relationship[0], existingID)


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
    sql = """SELECT FileIDs FROM FileIDsByFitsJhoveFormat where id = '%s'""" % (anID)
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 1:
        print >>sys.stderr, "Warning. More than one id for %s: %s" % (anID, rows.__str__())
    if len(rows):
        return rows[0][0]
    else:
        return False
    
#
def createNewID(newIDUUID, FileID, anID, fileUUID):
    #find the valid preservation/access status
    sql = """SELECT validPreservationFormat, validAccessFormat
                FROM FilesIdentifiedIDs 
                JOIN FileIDs ON FilesIdentifiedIDs.fileID = FileIDs.pk 
                WHERE FileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' 
                AND FilesIdentifiedIDs.fileUUID = '%s';""" % (fileUUID)
    rows = databaseInterface.queryAllSQL(sql) 
    if len(rows):
        validPreservationFormat, validAccessFormat = rows[0]
    else:
        validPreservationFormat, validAccessFormat = (False, False)
        
    
    description = anID
    fileIDType = 'b0bcccfb-04bc-4daa-a13c-77c23c2bda85'
    sql = """INSERT INTO FileIDs (pk, description, fileIDType, validPreservationFormat, validAccessFormat) VALUES ('%s', '%s', '%s', %s, %s);""" % (FileID, anID, fileIDType, validPreservationFormat, validAccessFormat)
    databaseInterface.runSQL(sql)
    
    sql = """INSERT INTO FileIDsByFitsJhoveFormat (pk, FileIDs, id) VALUES ('%s', '%s', '%s');""" % (newIDUUID, FileID, anID)
    databaseInterface.runSQL(sql)
    
    
#
def findRelationshipsForExtensionIDsForfileUUID(fileUUID):
    sql = """SELECT CommandRelationships.pk 
                FROM FilesIdentifiedIDs 
                JOIN FileIDs ON FilesIdentifiedIDs.fileID = FileIDs.pk 
                JOIN CommandRelationships ON CommandRelationships.fileID = FileIDs.pk 
                WHERE FileIDType = '16ae42ff-1018-4815-aac8-cceacd8d88a8' 
                AND FilesIdentifiedIDs.fileUUID = '%s';""" % (fileUUID)
    rows = databaseInterface.queryAllSQL(sql)
    return rows

#
def printResetCommands():
    print """#DELETE CommandRelationships FROM CommandRelationships JOIN FileIDs ON CommandRelationships.FileID = FileIDs.pk WHERE FileIDs.fileIDType = 'b0bcccfb-04bc-4daa-a13c-77c23c2bda85';

#DELETE FileIDsByFitsJhoveFormat FROM FileIDsByFitsJhoveFormat;

#DELETE FileIDs FROM FileIDs  WHERE FileIDs.fileIDType = 'b0bcccfb-04bc-4daa-a13c-77c23c2bda85';"""

if __name__ == '__main__':
    #printResetCommands()
    parser = OptionParser()
    parser.add_option("-F",  "--fileUUID",      action="store", dest="fileUUID", default="")
    parser.add_option("-S",  "--sipUUID",       action="store", dest="sipUUID", default="")
    parser.add_option("-T",  "--transferUUID",  action="store", dest="transferUUID", default="")

    (opts, args) = parser.parse_args()
    
    if not opts.fileUUID and not opts.sipUUID and not opts.transferUUID:
        sql = """SELECT fileUUID FROM Files;"""
        fileUUIDs = databaseInterface.queryAllSQL(sql)
        for fileUUID in fileUUIDs:
            identifyFromFileUUID(fileUUID[0], callWithIDs)
                
