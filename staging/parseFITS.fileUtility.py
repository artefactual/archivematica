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

databaseInterface.printSQL = True


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
        if element.get("name") == "file utility":
            for element2 in element.getiterator("format"):
                callWithIDs(element2.text, fileUUID)
                #print "\t", element2.text
    

def callWithIDs(anID, fileUUID):
    if not alreadyExistsCheck(anID):
        print "new id: ", anID
        newIDUUID = uuid.uuid4().__str__()
        newFileID = uuid.uuid4().__str__()
        createNewID(newIDUUID, newFileID, anID)
        
        
    for relationship in findRelationshipsForExtensionIDsForfileUUID(fileUUID):
        createNewReleationshipBasedOn(relationShip[0], anID)
            
def createNewReleationshipBasedOn(relationShip[0], anID):
    #find the command
    #see if there is already a relationship between this id and the command
    #if not, create the releationship
    
    #update is valid access/preservation
    print "TODO" 

def alreadyExistsCheck(anID):
    #check db for instances of this id
    sql = """SELECT pk FROM FileIDsByFitsFileUtilityFormat where id = '%s'""" % (anID)
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) > 1:
        print >>sys.stderr, "Warning. More than one id for %s: %s" % (anID, rows.__str__())
    if len(rows):
        return True
    else:
        return False
    
def createNewID(newIDUUID, FileID, anID):
    description = anID
    fileIDType = '076cce1b-9b46-4343-a193-11c2662c9e02'
    sql = """INSERT INTO FileIDs (pk, description, fileIDType) VALUES ('%s', '%s', '%s');""" % (FileID, anID, fileIDType)
    databaseInterface.runSQL(sql)
    
    sql = """INSERT INTO FileIDsByFitsFileUtilityFormat (pk, FileIDs, id) VALUES ('%s', '%s', '%s');""" % (newIDUUID, FileID, anID)
    databaseInterface.runSQL(sql)

if __name__ == '__main__':
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
                
