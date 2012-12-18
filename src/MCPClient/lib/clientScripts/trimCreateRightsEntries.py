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
import re
import os
from lxml import etree as etree
import sys
import traceback
import uuid
import string
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from externals.checksummingTools import md5_for_file
from fileOperations import getFileUUIDLike
import databaseFunctions
import databaseInterface

while False:
    import time
    time.sleep(10)

transferUUID = sys.argv[1]
transferName = sys.argv[2]
transferPath = sys.argv[3]
date = sys.argv[4]

currentDirectory = ""
exitCode = 0

def callWithException(exception):
    traceback

def getTimedeltaFromRetensionSchedule(RetentionSchedule):
    ret = 0
    rs = ["0"]
    rss = RetentionSchedule.split(".")
    for part in rss:
        entry = "0"
        for c in part:
            if c in string.digits:
                entry = "%s%s" % (entry, c)
        rs.append(entry)
    for entry in rs:
        ret += int (entry)
        
    ret = relativedelta(years=ret)
    return ret


def getDateTimeFromDateClosed(dateClosed):
    i = 19 #the + or minus for offset (DST + timezone)
    if dateClosed== None:
        return
    
    dateClosedDT = datetime.strptime(dateClosed[:i], '%Y-%m-%dT%H:%M:%S')
    print dateClosedDT     
    offSet = dateClosed[i+1:].split(":")
    offSetTD = timedelta(hours=int(offSet[0]), minutes=int(offSet[1]))

    if dateClosed[i] == "-":
        dateClosedDT = dateClosedDT - offSetTD
    elif  dateClosed[i] == "+":
        dateClosedDT = dateClosedDT + offSetTD
    else:
        print >>sys.stderr,"Error with offset in:", dateClosed
        return dateClosedDT
    return dateClosedDT
    
for dir in os.listdir(transferPath):
    dirPath = os.path.join(transferPath, dir)
    if not os.path.isdir(dirPath):
        continue
    
    xmlFilePath = os.path.join(dirPath, "ContainerMetadata.xml")
    try:
        tree = etree.parse(xmlFilePath)
        root = tree.getroot()
    except:
        print >>sys.stderr, "Error parsing: ", xmlFilePath.replace(transferPath, "%transferDirectory%", 1)
        exitCode += 1
        continue
    try:
        RetentionSchedule = root.find("Container/RetentionSchedule").text
        DateClosed = root.find("Container/DateClosed").text
    except:
        print >>sys.stderr, "Error retrieving values from: ", xmlFilePath.replace(transferPath, "%transferDirectory%", 1)
        exitCode += 1
        continue    
    
    retentionPeriod = getTimedeltaFromRetensionSchedule(RetentionSchedule)
    startTime = getDateTimeFromDateClosed(DateClosed)
    endTime = startTime + retentionPeriod
    
    indexForOnlyDate = 10
    startTime = startTime.__str__()[:indexForOnlyDate]
    endTime = endTime.__str__()[:indexForOnlyDate]
    
    for file in os.listdir(dirPath):
        filePath = os.path.join(dirPath, file)
        if  file == "ContainerMetadata.xml" or file.endswith("Metadata.xml") or not os.path.isfile(filePath):
            continue
        
        fileUUID = getFileUUIDLike(filePath, transferPath, transferUUID, "transferUUID", "%transferDirectory%")[filePath.replace(transferPath, "%transferDirectory%", 1)]
        FileMetadataAppliesToType = '7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17'
        
        #RightsStatement
        sql = """INSERT INTO RightsStatement SET 
            metadataAppliesToType='%s', 
            metadataAppliesToidentifier='%s',
            rightsStatementIdentifierType='UUID',
            rightsStatementIdentifierValue='%s',  
            fkAgent=1,
            rightsBasis='Other';""" % (FileMetadataAppliesToType, fileUUID, uuid.uuid4().__str__())
        RightsStatement = databaseInterface.insertAndReturnID(sql)
        
        #RightsStatementOtherRightsInformation
        sql = """INSERT INTO RightsStatementOtherRightsInformation SET 
            fkRightsStatement=%d,
            otherRightsBasis='Policy',
            otherRightsApplicableStartDate='',
            otherRightsApplicableEndDate='';""" % (RightsStatement)
        RightsStatementOtherRightsInformation = databaseInterface.insertAndReturnID(sql)
        
        #RightsStatementOtherRightsDocumentationIdentifier
        sql = """INSERT INTO RightsStatementOtherRightsDocumentationIdentifier SET
              fkRightsStatementOtherRightsInformation=%d,
              otherRightsDocumentationIdentifierType='',
              otherRightsDocumentationIdentifierValue='',
              otherRightsDocumentationIdentifierRole='';""" % (RightsStatementOtherRightsInformation)
        RightsStatementOtherRightsDocumentationIdentifier = databaseInterface.insertAndReturnID(sql)
        
        #RightsStatementRightsGranted
        sql = """INSERT INTO RightsStatementRightsGranted SET
            fkRightsStatement=%d,
            act='Disseminate',
            startDate='%s',
            endDate='%s';""" % (RightsStatement, startTime, endTime)
        RightsStatementRightsGranted = databaseInterface.insertAndReturnID(sql)
        
        #RightsStatementRightsGrantedNote
        sql = """INSERT INTO RightsStatementRightsGrantedNote SET
            fkRightsStatementRightsGranted=%d,
            rightsGrantedNote='%s';""" % (RightsStatementRightsGranted,"Closed until %s" % (endTime))
        RightsStatementRightsGrantedNote = databaseInterface.insertAndReturnID(sql)
        
        #RightsStatementRightsGrantedRestriction
        sql = """INSERT INTO RightsStatementRightsGrantedRestriction SET
        fkRightsStatementRightsGranted=%d,
        restriction='Disallow';""" % (RightsStatementRightsGranted)
        RightsStatementRightsGrantedRestriction = databaseInterface.insertAndReturnID(sql)
        
                 
quit(exitCode)
