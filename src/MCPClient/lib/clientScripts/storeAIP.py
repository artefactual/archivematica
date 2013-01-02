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
import sys
import os
import stat
import shutil
import MySQLdb
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
import databaseInterface


printSubProcessOutput=True

AIPsStore = sys.argv[1]
AIP = sys.argv[2]
SIPUUID = sys.argv[3]
HTMLFilePath = sys.argv[4]
SIPNAME = sys.argv[5]
SIPDATE = sys.argv[6]

#Get the UUID quads
uuidQuads = []
SIPUUIDStripped = SIPUUID.replace("-","")
uuidQuads.append(SIPUUIDStripped[:4])
uuidQuads.append(SIPUUIDStripped[4:7])
uuidQuads.append(SIPUUIDStripped[8:12])
uuidQuads.append(SIPUUIDStripped[12:16])
uuidQuads.append(SIPUUIDStripped[16:20])
uuidQuads.append(SIPUUIDStripped[20:24])
uuidQuads.append(SIPUUIDStripped[24:28])
uuidQuads.append(SIPUUIDStripped[28:32])

AIPsStoreWithQuads = AIPsStore
mode= stat.S_IWUSR + stat.S_IRUSR + stat.S_IXUSR + stat.S_IRGRP + stat.S_IXGRP + stat.S_IXOTH + stat.S_IROTH
for quad in uuidQuads:
    AIPsStoreWithQuads = AIPsStoreWithQuads + quad + "/"
    if not os.path.isdir(AIPsStoreWithQuads):
        os.mkdir(AIPsStoreWithQuads, mode)
        #mode isn't working on the mkdir
        os.chmod(AIPsStoreWithQuads, mode)

storeLocation=os.path.join(AIPsStoreWithQuads, os.path.basename(os.path.abspath(AIP)))

#Store the AIP
shutil.move(AIP, storeLocation)

#Extract the AIP
extractDirectory = "/tmp/" + SIPUUID + "/"
os.makedirs(extractDirectory)
#
command = "7z x -bd -o\"" + extractDirectory + "\" \"" + storeLocation + "\""
ret = executeOrRun("command", command, printing=printSubProcessOutput)
exitCode, stdOut, stdErr = ret
if exitCode != 0:
    print >>sys.stderr, "Error extracting"
    quit(1)

bag = extractDirectory + SIPNAME + "-" + SIPUUID + "/"
verificationCommands = []
verificationCommands.append("/usr/share/bagit/bin/bag verifyvalid \"" + bag + "\"")
verificationCommands.append("/usr/share/bagit/bin/bag checkpayloadoxum \"" + bag + "\"")
verificationCommands.append("/usr/share/bagit/bin/bag verifycomplete \"" + bag + "\"")
verificationCommands.append("/usr/share/bagit/bin/bag verifypayloadmanifests \"" + bag + "\"")
verificationCommands.append("/usr/share/bagit/bin/bag verifytagmanifests \"" + bag + "\"")
exitCode = 0
for command in verificationCommands:
    ret = executeOrRun("command", command, printing=printSubProcessOutput)
    exit, stdOut, stdErr = ret
    if exit != 0:
        print >>sys.stderr, "Failed test: ", command
        exitCode=1
    else:
        print >>sys.stderr, "Passed test: ", command

#copy thumbnails to an AIP-specific directory for easy admin access
thumbnailSourceDir = os.path.join(bag, 'data/thumbnails')
thumbnailDestDir   = os.path.join(AIPsStore, 'thumbnails', SIPUUID)

#create thumbnail dest dir
if not os.path.exists(thumbnailDestDir):
    os.makedirs(thumbnailDestDir)

#copy thumbnails to destination directory
thumbnails = os.listdir(thumbnailSourceDir)
for filename in thumbnails:
    shutil.copy(os.path.join(thumbnailSourceDir, filename), thumbnailDestDir)

#cleanup
shutil.rmtree(extractDirectory)

#write to database
sql = """INSERT INTO AIPs (sipUUID, sipName, sipDate, filePath) VALUES ('%s', '%s', '%s', '%s')""" % (MySQLdb.escape_string(SIPUUID), MySQLdb.escape_string(SIPNAME), MySQLdb.escape_string(SIPDATE), MySQLdb.escape_string(storeLocation))
databaseInterface.runSQL(sql)

quit(exitCode)
