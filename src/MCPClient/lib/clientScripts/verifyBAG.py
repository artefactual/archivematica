#!/usr/bin/env python2

import os
import sys
# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun

logger = get_script_logger("archivematica.mcp.client.verifyBAG")

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

