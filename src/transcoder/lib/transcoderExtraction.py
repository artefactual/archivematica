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

import sys
import os
import uuid
from transcoder import main
from executeOrRunSubProcess import executeOrRun
import transcoder
#from premisXMLlinker import xmlNormalize
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import addFileToTransfer
from databaseFunctions import fileWasRemoved
from fileOperations import updateSizeAndChecksum
import databaseInterface

global extractedCount
extractedCount = 1
removeOnceExtracted = True

date = sys.argv[4].__str__().split(".", 1)[0]
replacementDic = { \
        "%inputFile%": transcoder.fileFullName, \
        "%outputDirectory%": transcoder.fileFullName + '-' + date \
        }

def onceExtracted(command):
    extractedFiles = []
    print "TODO - Metadata regarding removal of extracted archive"
    if removeOnceExtracted:
        packageFileUUID = sys.argv[6].__str__()
        sipDirectory = sys.argv[2].__str__()
        os.remove(replacementDic["%inputFile%"])
        currentLocation =  replacementDic["%inputFile%"].replace(sipDirectory, "%transferDirectory%", 1)
        fileWasRemoved(packageFileUUID, eventOutcomeDetailNote = "removed from: " + currentLocation)

    print "OUTPUT DIRECTORY: ", replacementDic["%outputDirectory%"]
    for w in os.walk(replacementDic["%outputDirectory%"].replace("*", "asterisk*")):
        path, directories, files = w
        for p in files:
            p = os.path.join(path, p)
            #print "path: ", p
            if os.path.isfile(p):
                extractedFiles.append(p)
    for ef in extractedFiles:
        fileUUID = uuid.uuid4().__str__()
        #print "File Extracted:", ef
        if True: #Add the file to the SIP
            #<arguments>"%relativeLocation%" "%SIPObjectsDirectory%" "%SIPLogsDirectory%" "%date%" "%taskUUID%" "%fileUUID%"</arguments>
            sipDirectory = sys.argv[2].__str__()
            transferUUID = sys.argv[3].__str__()
            date = sys.argv[4].__str__()
            taskUUID = sys.argv[5].__str__()
            packageFileUUID = sys.argv[6].__str__()

            filePathRelativeToSIP = ef.replace(sipDirectory,"%transferDirectory%", 1)
            print "File Extracted:: {" + fileUUID + "} ", filePathRelativeToSIP
            eventDetail="Unpacked from: {" + packageFileUUID + "}" + filePathRelativeToSIP
            addFileToTransfer(filePathRelativeToSIP, fileUUID, transferUUID, taskUUID, date, sourceType="unpacking", eventDetail=eventDetail)
            updateSizeAndChecksum(fileUUID, ef, date, uuid.uuid4.__str__())


        run = sys.argv[0].__str__() + \
        " \"" + transcoder.escapeForCommand(ef) + "\""
        if True: #Add the file to the SIP
            run = run + " \"" + transcoder.escapeForCommand(sys.argv[2].__str__()) + "\"" + \
            " \"" + transcoder.escapeForCommand(sys.argv[3].__str__()) + "\"" + \
            " \"" + transcoder.escapeForCommand(sys.argv[4].__str__()) + "\"" + \
            " \"" + transcoder.escapeForCommand(sys.argv[5].__str__()) + "\"" + \
            " \"" + fileUUID + "\""

        exitCode, stdOut, stdError = executeOrRun("command", run)
        print stdOut
        print >>sys.stderr, stdError
        if exitCode != 0 and command.exitCode == 0:
            command.exitCode = exitCode

    global extractedCount
    date = sys.argv[4].__str__().split(".", 1)[0]
    extractedCount = extractedCount + 1
    replacementDic["%outputDirectory%"] = transcoder.fileFullName + '-' + extractedCount.__str__() + '-' + date

def identifyCommands(fileName):
    """Identify file type(s)"""
    ret = []
    removeOnceExtractedSkip = ['.part01.rar', '.r01', '.pst']

    RarExtensions = ['.part01.rar', '.r01', '.rar']
    for extension in RarExtensions:
        if fileName.lower().endswith(extension.lower()):
            #sql find the file type,
            sql = """SELECT CR.pk, CR.command, CR.GroupMember
            FROM CommandRelationships AS CR
            JOIN FileIDs ON CR.fileID=FileIDs.pk
            JOIN CommandClassifications ON CR.commandClassification = CommandClassifications.pk
            WHERE FileIDs.description='unrar-nonfreeCompatable'
            AND CommandClassifications.classification = 'extract';"""
            databaseInterface.runSQL(sql)
            while row != None:
                ret.append(row)
                row = c.fetchone()
            break

    SevenZipExtensions = ['.ARJ', '.CAB', '.CHM', '.CPIO',
                  '.DMG', '.HFS', '.LZH', '.LZMA',
                  '.NSIS', '.UDF', '.WIM', '.XAR',
                  '.Z', '.ZIP', '.GZIP', '.TAR',]
    for extension in SevenZipExtensions:
        if fileName.lower().endswith(extension.lower()):
            sql = """SELECT CR.pk, CR.command, CR.GroupMember
            FROM CommandRelationships AS CR
            JOIN FileIDs ON CR.fileID=FileIDs.pk
            JOIN CommandClassifications ON CR.commandClassification = CommandClassifications.pk
            WHERE FileIDs.description='7ZipCompatable'
            AND CommandClassifications.classification = 'extract';"""
            databaseInterface.runSQL(sql)
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            while row != None:
                ret.append(row)
                row = c.fetchone()
            sqlLock.release()
            break
    if fileName.lower().endswith('.pst'):
        global removeOnceExtracted
        sql = """SELECT CR.pk, CR.command, CR.GroupMember
        FROM CommandRelationships AS CR
        JOIN FileIDs ON CR.fileID=FileIDs.pk
        JOIN CommandClassifications ON CR.commandClassification = CommandClassifications.pk
        WHERE FileIDs.description='A .pst file'
        AND CommandClassifications.classification = 'extract';"""
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            ret.append(row)
            row = c.fetchone()
        sqlLock.release()

    #check if not to remove
    for extension in removeOnceExtractedSkip:
        if fileName.lower().endswith(extension.lower()):
            removeOnceExtracted = False
            break
    return ret

if __name__ == '__main__':
    #while 1:
    #    import time
    #    time.sleep(10)
    transcoder.onSuccess = onceExtracted
    transcoder.identifyCommands = identifyCommands
    transcoder.replacementDic = replacementDic
    filename = sys.argv[1].__str__()
    print filename
    main(filename)
