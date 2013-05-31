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
import shlex
import lxml.etree as etree
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from archivematicaFunctions import getTagged
from archivematicaFunctions import escapeForCommand
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoFilesIDs
import databaseInterface

databaseInterface.printSQL = False
tikaPath = "/usr/bin/tika"

def getTikaVersion():
    command = "%s -V" % (tikaPath) 
    exitCode, stdOut, stdErr = executeOrRun("command", command, printing=False)
    if exitCode != 0:
        print >>sys.stderr, "Error: ", stdOut, stdErr, exitCode
        return ""
    return stdOut.strip().replace("Apache Tika ", "")
    
def getTikaID(itemdirectoryPath):
    command = "%s -x -d %s" % (tikaPath, itemdirectoryPath) 
    exitCode, stdOut, stdErr = executeOrRun("command", command, printing=False)
    if exitCode == 1: #no id found
        print >>sys.stderr, "Tika found no format id"
        exit(0)
    if exitCode != 0:
        print >>sys.stderr, "Error: ", stdOut, stdErr, exitCode
        return ""
    return stdOut.strip()

def getArchivematicaFileID(tikaFileID, tikaVersion):
    sql = """SELECT fileID FROM FileIDsBySingleID 
            WHERE 
                tool = 'Tika' 
                AND toolVersion = '%s'
                AND id='%s';""" % (tikaVersion, tikaFileID)
    ret = databaseInterface.queryAllSQL(sql)
    if not len(ret):
        print >>sys.stderr, "No Archivematica format id for Tika %s: %s" % (tikaVersion, tikaFileID)
        exit(0)
    return ret[0][0]

def parseArgs():
    from optparse import OptionParser
    #--fileUUID "%fileUUID%" --SIPUUID "%SIPUUID%" --filePath "%relativeLocation%" --eventIdentifierUUID "%taskUUID%" --date "%date%"
    parser = OptionParser()
    parser.add_option("-s",  "--SIPUUID", action="store", dest="SIPUUID", default="")
    parser.add_option("-f",  "--filePath", action="store", dest="filePath", default="") 
    parser.add_option("-u",  "--fileUUID", action="store", dest="fileUUID", default="")
    parser.add_option("-e",  "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    parser.add_option("-d",  "--date", action="store", dest="date", default='')
    parser.add_option("-g",  "--fileGrpUse", action="store", dest="fileGrpUse", default='')
    return parser.parse_args()
    
def insertIntoFileIds(fileUUID, fileID):
    sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', '%s');""" % (fileUUID, fileID)
    databaseInterface.runSQL(sql)

if __name__ == '__main__':
    (opts, args) = parseArgs() 
    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)
    
    if opts.fileGrpUse in ["DSPACEMETS", "maildirFile"]:
        print "file's fileGrpUse in exclusion list, skipping"
        exit(0)
        
    tikaFileID = getTikaID(opts.filePath)
    tikaVersion = getTikaVersion()
    fileID = getArchivematicaFileID(tikaFileID, tikaVersion)
    print "Found file ID {%s}: %s" % (fileID, tikaFileID) 
    insertIntoFileIds(opts.fileUUID, fileID)
    
    eventDetailText = 'program="Tika"; version="%s"' % (tikaVersion)
    eventOutcomeText='Positive'
    eventOutcomeDetailNote=tikaFileID
    insertIntoEvents(fileUUID=opts.fileUUID, \
                         eventIdentifierUUID=uuid.uuid4().__str__(), \
                         eventType="format identification", \
                         eventDateTime=opts.date, \
                         eventDetail=eventDetailText, \
                         eventOutcome=eventOutcomeText, \
                         eventOutcomeDetailNote=eventOutcomeDetailNote)
    
    
    

