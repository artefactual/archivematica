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
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from restructureForCompliance import restructureBagForComplianceFileUUIDsAssigned
from databaseFunctions import insertIntoEvents
import databaseInterface

printSubProcessOutput=False
exitCode = 0
verificationCommands = []
verificationCommandsOutputs = []

def verifyBag(bag):
    global exitCode
    verificationCommands = [
        "/usr/share/bagit/bin/bag verifyvalid \"" + bag + "\"", 
        "/usr/share/bagit/bin/bag checkpayloadoxum \"" + bag + "\"", 
        "/usr/share/bagit/bin/bag verifycomplete \"" + bag + "\"", 
        "/usr/share/bagit/bin/bag verifypayloadmanifests \"" + bag + "\"", 
        "/usr/share/bagit/bin/bag verifytagmanifests \"" + bag + "\"" ]
    for command in verificationCommands:
        ret = executeOrRun("command", command, printing=printSubProcessOutput)
        verificationCommandsOutputs.append(ret)
        exit, stdOut, stdErr = ret
        if exit != 0:
            print >>sys.stderr, "Failed test: ", command
            print >>sys.stderr, stdErr
            print >>sys.stderr
            exitCode += 1
        else:
            print "Passed test: ", command
    
if __name__ == '__main__':
    target = sys.argv[1]
    transferUUID =  sys.argv[2]
    verifyBag(target)
    if exitCode != 0:
        print >>sys.stderr, "Failed bagit compliance. Not restructuring."
        exit(exitCode) 
    restructureBagForComplianceFileUUIDsAssigned(target, transferUUID, "transferUUID")
    for i in range(len(verificationCommands)):
        print verificationCommands[i]
        print verificationCommandsOutputs[i]
        print
        
    sql = "SELECT Files.fileUUID FROM Files WHERE removedTime = 0 AND Files.currentLocation LIKE '\%transferDirectory\%objects/%' AND transferUUID = '" + transferUUID + "';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        insertIntoEvents(fileUUID=row[0], \
                     eventType="fixity check", \
                     eventDetail="Bagit - verifypayloadmanifests", \
                     eventOutcome="Pass")
    
    exit(exitCode)
