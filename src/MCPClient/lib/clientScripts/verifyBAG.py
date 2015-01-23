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
# archivematicaCommon
from executeOrRunSubProcess import executeOrRun

printSubProcessOutput=True

bag = sys.argv[1]
verificationCommands = []
verificationCommands.append("/usr/share/bagit/bin/bag verifyvalid \"%s\"" % (bag)) #Verifies the validity of a bag.
verificationCommands.append("/usr/share/bagit/bin/bag verifycomplete \"%s\"" % (bag)) #Verifies the completeness of a bag.
verificationCommands.append("/usr/share/bagit/bin/bag verifypayloadmanifests \"%s\"" % (bag)) #Verifies the checksums in all payload manifests.

bagInfoPath = os.path.join(bag, "bag-info.txt")
if os.path.isfile(bagInfoPath):
    for line in open(bagInfoPath,'r'):
        if line.startswith("Payload-Oxum"):
            verificationCommands.append("/usr/share/bagit/bin/bag checkpayloadoxum \"%s\"" % (bag)) #Generates Payload-Oxum and checks against Payload-Oxum in bag-info.txt.
            break

for item in os.listdir(bag):
    if item.startswith("tagmanifest-") and item.endswith(".txt"):        
        verificationCommands.append("/usr/share/bagit/bin/bag verifytagmanifests \"%s\"" % (bag)) #Verifies the checksums in all tag manifests.
        break
        
exitCode = 0
for command in verificationCommands:
    ret = executeOrRun("command", command, printing=printSubProcessOutput)
    exit, stdOut, stdErr = ret
    if exit != 0:
        print >>sys.stderr, "Failed test: ", command
        exitCode=1
    else:
        print >>sys.stderr, "Passed test: ", command
quit(exitCode)

