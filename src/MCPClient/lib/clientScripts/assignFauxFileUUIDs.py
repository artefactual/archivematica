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
import uuid
from lxml import etree
# archivematicaCommon
from fileOperations import addFileToSIP
import databaseInterface

def assignFauxFileUUIDs(unitPath, mets, unitUUID, date):
    metsNameSpace = "http://www.loc.gov/METS/"
    xlinkNameSpace = "http://www.w3.org/1999/xlink"
    uuidLen = 36
    fileSec = mets.find("{%s}%s" % (metsNameSpace, "fileSec"))
    for fileGrp in fileSec.findall("{%s}%s" % (metsNameSpace, "fileGrp")):
        use = fileGrp.get("USE")
        for file in fileGrp.findall("{%s}%s" % (metsNameSpace, "file")):
            ID = file.get("ID")
            originalUUID = ID[-(uuidLen):]
            
            GROUPID = file.get("GROUPID")
            originalGroupUUID = GROUPID[-(uuidLen):]
            
            FLocat = file.find("{%s}%s" % (metsNameSpace, "FLocat"))
            href = FLocat.get("{%s}%s" % (xlinkNameSpace, "href"))
            filePath = os.path.join(unitPath, href)
            relativeFilePath = "%SIPDirectory%" + href
            if not os.path.isfile(filePath):
                print >>sys.stderr, "File missing: ", relativeFilePath
                continue
            
            newFileUUID = str(uuid.uuid4())
            print  originalUUID, " -> ", newFileUUID, relativeFilePath
            print originalUUID
            print originalGroupUUID
            print relativeFilePath
            print use
            print
            
            databaseInterface.runSQL("""INSERT INTO Files (fileUUID, originalLocation, currentLocation, enteredSystem, fileGrpUse, fileGrpUUID, sipUUID)
                VALUES ( '"""   + newFileUUID + databaseInterface.separator \
                                + databaseInterface.MySQLdb.escape_string(relativeFilePath) + databaseInterface.separator \
                                + databaseInterface.MySQLdb.escape_string(relativeFilePath) + databaseInterface.separator \
                                + date + databaseInterface.separator \
                                + use + databaseInterface.separator \
                                + originalGroupUUID + databaseInterface.separator \
                                + unitUUID + "' );" )
            sql = """INSERT INTO FauxFileIDsMap SET  fauxSIPUUID='%s', fauxFileUUID='%s', fileUUID='%s';""" % (unitUUID, newFileUUID, originalUUID)
            databaseInterface.runSQL(sql)
            

if __name__ == '__main__':
    fauxUUID = sys.argv[1]
    unitPath = sys.argv[2]
    date = sys.argv[3]
    
    basename = os.path.basename(unitPath[:-1])
    uuidLen = 36
    originalSIPName = basename[:-(uuidLen+1)*2]
    originalSIPUUID = basename[:-(uuidLen+1)][-uuidLen:]
    METSPath = os.path.join(unitPath, "metadata/submissionDocumentation/data/", "METS.%s.xml" % (originalSIPUUID))
    if not os.path.isfile(METSPath):
        print >>sys.stderr, "Mets file not found: ", METSPath
        exit(-1)
        
    parser = etree.XMLParser(remove_blank_text=True)
    metsTree = etree.parse(METSPath, parser)
    mets = metsTree.getroot()
    
    assignFauxFileUUIDs(unitPath, mets, fauxUUID, date)