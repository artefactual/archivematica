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
from transcoder import main
from transcoder import setFileIn
from optparse import OptionParser
import transcoder
import uuid
#from premisXMLlinker import xmlNormalize
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import addFileToSIP
from fileOperations import updateSizeAndChecksum
from getPronomsFromPremis import getPronomsFromPremis
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoDerivations
import databaseInterface


global replacementDic
global opts
global outputFileUUID
global outputFileUUIDHasBeenTaskUUID
outputFileUUIDHasBeenTaskUUID = False

def inAccessFormat():
    ex=["CSS", "CSV", "DOCX", "HTML", "LOG", "ODS", "TXT", "XML", "XSL", "XLS", "XLSX", \
        "MP3", "PDF", "JPG", "MPG" ]
    return transcoder.fileExtension.__str__().upper() in ex

def inPreservationFormat():
    ex=["CSS", "CSV", "DOC", "DOCX", "HTML", "LOG", "PPT", "TXT", "XML", "XLS", "XLSX", "LOG", \
        "JP2", "PNG", \
        "SVG", "WAV", "TIF", "TIFF", "PDF", "ODG", "ODP", "MKV", "MXF", "ODT", "ODS", "MBOX", "MBOXI", "AI", \
    "PPTX", \
    "DNG" ]
    return transcoder.fileExtension.__str__().upper() in ex

def onceNormalized(command):
    transcodedFiles = []
    if not command.outputLocation:
        command.outputLocation = ""
    elif os.path.isfile(command.outputLocation):
        transcodedFiles.append(command.outputLocation)
    elif os.path.isdir(command.outputLocation):
        for w in os.walk(command.outputLocation):
            path, directories, files = w
            for p in files:
                p = os.path.join(path, p)
                if os.path.isfile(p):
                    transcodedFiles.append(p)
    elif command.outputLocation:
        print >>sys.stderr, command
        print >>sys.stderr, "Error - output file does not exist [" + command.outputLocation + "]"
        command.exitCode = -2

    derivationEventUUID = uuid.uuid4().__str__()
    for ef in transcodedFiles:
        global outputFileUUID
        global replacementDic
        global opts
        if opts.commandClassifications == "preservation":
            old = """xmlNormalize(outputFileUUID, \
                     ef, \
                     command.eventDetailCommand.stdOut, \
                     opts.fileUUID, \
                     opts.objectsDirectory, \
                     opts.taskUUID, \
                     opts.date, \
                     opts.logsDirectory, \
                     ) #    {normalized; not normalized}"""

            #Add the new file to the sip
            filePathRelativeToSIP = ef.replace(opts.sipPath, "%SIPDirectory%", 1)
            # addFileToSIP(filePathRelativeToSIP, fileUUID, sipUUID, taskUUID, date, sourceType="ingestion"):
            addFileToSIP(filePathRelativeToSIP, outputFileUUID, opts.sipUUID, uuid.uuid4().__str__(), opts.date, sourceType="creation", use="preservation")
            #Calculate new file checksum
            print >>sys.stderr, "TODO: calculate new file checksum"
            #Add event information to current file
            insertIntoEvents(fileUUID=opts.fileUUID, \
               eventIdentifierUUID=derivationEventUUID, \
               eventType="normalization", \
               eventDateTime=opts.date, \
               eventDetail=command.eventDetailCommand.stdOut, \
               eventOutcome="", \
               eventOutcomeDetailNote=filePathRelativeToSIP)

            updateSizeAndChecksum(outputFileUUID, ef, opts.date, uuid.uuid4().__str__())

            #Add linking information between files
            insertIntoDerivations(sourceFileUUID=opts.fileUUID, derivedFileUUID=outputFileUUID, relatedEventUUID=derivationEventUUID)

            outputFileUUID = uuid.uuid4().__str__()
            replacementDic["%postfix%"] = "-" + outputFileUUID

def identifyCommands(fileName):
    """Identify file type(s)"""
    ret = []
    premisFile = opts.logsDirectory + "fileMeta/" + opts.fileUUID + ".xml"
    try:
        for pronomID in getPronomsFromPremis(premisFile):
            sql = """SELECT CR.pk, CR.command, CR.GroupMember
            FROM CommandRelationships AS CR
            JOIN FileIDs ON CR.fileID=FileIDs.pk
            JOIN CommandClassifications ON CR.commandClassification = CommandClassifications.pk
            JOIN FileIDsByPronom AS FIBP  ON FileIDs.pk = FIBP.FileIDs
            WHERE FIBP.FileID = '""" + pronomID.__str__() + """'
            AND CommandClassifications.classification = '""" + opts.commandClassifications +"""';"""
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            while row != None:
                ret.append(row)
                row = c.fetchone()
            sqlLock.release()
    except:
        print >>sys.stderr, "Failed to retrieve pronomIDs."
        ret = []

    if transcoder.fileExtension:
        sql = """SELECT CR.pk, CR.command, CR.GroupMember
        FROM CommandRelationships AS CR
        JOIN FileIDs ON CR.fileID=FileIDs.pk
        JOIN CommandClassifications ON CR.commandClassification = CommandClassifications.pk
        JOIN FileIDsByExtension AS FIBE  ON FileIDs.pk = FIBE.FileIDs
        WHERE FIBE.Extension = '""" + transcoder.fileExtension.__str__() + """'
        AND CommandClassifications.classification = '""" + opts.commandClassifications +"""';"""
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            ret.append(row)
            row = c.fetchone()
        sqlLock.release()

    if not len(ret):
        if opts.commandClassifications == "preservation":
            if inPreservationFormat():
                print "Already in preservation format."
            else:
                print >>sys.stderr, "Unable to verify archival readiness."
                #Issue 528: related to exit code
                exit(0)

        elif opts.commandClassifications == "access":
            sql = """SELECT CR.pk, CR.command, CR.GroupMember
            FROM CommandRelationships AS CR
            JOIN Commands AS C ON CR.command = C.pk
            WHERE C.description = 'Copying file to access directory.';"""
            rows = databaseInterface.queryAllSQL(sql)
            for row in rows:
                cl = transcoder.CommandLinker(row)
                copyExitCode = cl.execute()
                if copyExitCode:
                    exit(copyExitCode)
            if inAccessFormat():
                print "Already in access format."
                exit(0)
            else:
                print >>sys.stderr, "Unable to verify access readiness."
                #Issue 528: related to exit code
                exit(0)
        
        elif opts.commandClassifications == "thumbnail":
            #use default thumbnail
            print "Using default thumbnail"
            sql = """SELECT CR.pk, CR.command, CR.GroupMember
            FROM CommandRelationships AS CR
            JOIN Commands AS C ON CR.command = C.pk
            WHERE C.description = 'Using default thumbnail.';"""
            rows = databaseInterface.queryAllSQL(sql)
            for row in rows:
                cl = transcoder.CommandLinker(row)
                copyExitCode = cl.execute()
                exit(copyExitCode)
                
    return ret

if __name__ == '__main__':
    global opts
    global replacementDic
    global outputFileUUID

    parser = OptionParser()
    parser.add_option("-f",  "--inputFile",          action="store", dest="inputFile", default="")
    parser.add_option("-c",  "--commandClassifications",  action="store", dest="commandClassifications", default="")
    parser.add_option("-i",  "--fileUUID",           action="store", dest="fileUUID", default="")
    parser.add_option("-t",  "--taskUUID",           action="store", dest="taskUUID", default="")
    parser.add_option("-o",  "--objectsDirectory",   action="store", dest="objectsDirectory", default="")
    parser.add_option("-l",  "--logsDirectory",      action="store", dest="logsDirectory", default="")
    parser.add_option("-a",  "--accessDirectory",    action="store", dest="accessDirectory", default="")
    parser.add_option("-b",  "--thumbnailDirectory",    action="store", dest="thumbnailDirectory", default="")
    parser.add_option("-e",  "--excludeDirectory",    action="store", dest="excludeDirectory", default="")
    parser.add_option("-d",  "--date",   action="store", dest="date", default="")
    parser.add_option("-s",  "--sipUUID",   action="store", dest="sipUUID", default="")
    parser.add_option("-p",  "--sipPath",   action="store", dest="sipPath", default="")
    parser.add_option("-g",  "--fileGrpUse",   action="store", dest="fileGrpUse", default="")
    parser.add_option("-n",  "--normalizeFileGrpUse",   action="store", dest="normalizeFileGrpUse", default="original")

    (opts, args) = parser.parse_args()

    filename = opts.inputFile
    print "Operating on file: ", filename
    print "Using " + opts.commandClassifications + " command classifications"

    if opts.excludeDirectory != "":
        if filename.startswith(opts.excludeDirectory):
            print "skipping file in exclude directory: ", filename
            exit(0)

    #can move into if opts.commandClassifications == "preservation/access": to isolate for those functions
    if opts.fileGrpUse != opts.normalizeFileGrpUse:
        print "file's fileGrpUse not part of normalize from use."
        exit(0)

    setFileIn(fileIn=filename)
    prefix = ""
    postfix = ""
    outputDirectory = ""
    if opts.commandClassifications == "preservation":
        postfix = "-" + opts.taskUUID
        outputFileUUID = opts.taskUUID
        outputDirectory = transcoder.fileDirectory
    elif opts.commandClassifications == "access":
        prefix = opts.fileUUID + "-"
        outputDirectory = opts.accessDirectory
    elif opts.commandClassifications == "thumbnail":
        outputDirectory = opts.thumbnailDirectory
        postfix = opts.fileUUID
    else:
        print >>sys.stderr, "Unsupported command classification."
        exit(2)

    fileExtensionWithDot = "." + transcoder.fileExtension
    if transcoder.fileExtension == "":
        fileExtensionWithDot = ""
    replacementDic = { \
        "%inputFile%": transcoder.fileFullName, \
        "%outputDirectory%": outputDirectory, \
        "%fileExtension%": transcoder.fileExtension, \
        "%fileExtensionWithDot%": fileExtensionWithDot, \
        "%fileFullName%": transcoder.fileFullName, \
        "%preservationFileDirectory%": transcoder.fileDirectory, \
        "%fileDirectory%": transcoder.fileDirectory,\
        "%fileTitle%": transcoder.fileTitle, \
        "%fileName%":  transcoder.fileTitle, \
        "%prefix%": prefix,
        "%postfix%": postfix
        }


    transcoder.onSuccess = onceNormalized
    transcoder.identifyCommands = identifyCommands
    transcoder.replacementDic = replacementDic
    main(filename)
