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

#source /etc/archivematica/archivematicaConfig.conf
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import insertIntoEvents
from archivematicaFunctions import escapeForCommand

clamscanResultShouldBe="Infected files: 0"

if __name__ == '__main__':
    fileUUID = sys.argv[1]
    target =  sys.argv[2]
    date = sys.argv[3]
    taskUUID = sys.argv[4]

    command = 'clamdscan  - <"' + escapeForCommand(target) + '"'
    print >>sys.stderr, command
    commandVersion = "clamdscan -V"
    eventOutcome = "Pass"

    clamscanOutput = executeOrRun("bashScript", command, printing=False)
    clamscanVersionOutput = executeOrRun("command", commandVersion, printing=False)

    if clamscanOutput[0] or clamscanVersionOutput[0]:
        if clamscanVersionOutput[0]:
            print >>sys.stderr, clamscanVersionOutput
            exit(2)
        else:
            eventOutcome = "Fail"

    if eventOutcome == "Fail" or clamscanOutput[1].find(clamscanResultShouldBe) == -1:
        eventOutcome = "Fail"
        print >>sys.stderr, fileUUID, " - ", os.path.basename(target)
        print >>sys.stderr, clamscanOutput

    version, virusDefs, virusDefsDate = clamscanVersionOutput[1].split("/")
    virusDefs = virusDefs + "/" + virusDefsDate
    eventDetailText = "program=\"Clam AV\"; version=\"" + version + "\"; virusDefinitions=\"" + virusDefs + "\""

    if fileUUID != "None":
        insertIntoEvents(fileUUID=fileUUID, eventIdentifierUUID=taskUUID, eventType="virus check", eventDateTime=date, eventDetail=eventDetailText, eventOutcome=eventOutcome, eventOutcomeDetailNote="")
    if eventOutcome != "Pass":
        exit(3)
