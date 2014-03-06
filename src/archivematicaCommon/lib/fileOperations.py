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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

import csv
import os
import uuid
import sys
import databaseInterface
import shutil
from databaseFunctions import insertIntoFiles
from executeOrRunSubProcess import executeOrRun
from externals.checksummingTools import sha_for_file
from databaseFunctions import insertIntoEvents
import MySQLdb
from archivematicaFunctions import unicodeToStr

def updateSizeAndChecksum(fileUUID, filePath, date, eventIdentifierUUID):
    fileSize = os.path.getsize(filePath).__str__()
    checksum = sha_for_file(filePath).__str__()

    sql = "UPDATE Files " + \
        "SET fileSize='" + fileSize +"', checksum='" + checksum +  "' " + \
        "WHERE fileUUID='" + fileUUID + "'"
    databaseInterface.runSQL(sql)

    insertIntoEvents(fileUUID=fileUUID, \
                     eventIdentifierUUID=eventIdentifierUUID, \
                     eventType="message digest calculation", \
                     eventDateTime=date, \
                     eventDetail="program=\"python\"; module=\"hashlib.sha256()\"", \
                     eventOutcomeDetailNote=checksum)


def addFileToTransfer(filePathRelativeToSIP, fileUUID, transferUUID, taskUUID, date, sourceType="ingestion", eventDetail="", use="original"):
    #print filePathRelativeToSIP, fileUUID, transferUUID, taskUUID, date, sourceType, eventDetail, use
    insertIntoFiles(fileUUID, filePathRelativeToSIP, date, transferUUID=transferUUID, use=use)
    insertIntoEvents(fileUUID=fileUUID, \
                   eventIdentifierUUID=taskUUID, \
                   eventType=sourceType, \
                   eventDateTime=date, \
                   eventDetail=eventDetail, \
                   eventOutcome="", \
                   eventOutcomeDetailNote="")
    addAccessionEvent(fileUUID, transferUUID, date)

def addAccessionEvent(fileUUID, transferUUID, date):
    
    sql = """SELECT accessionID FROM Transfers WHERE transferUUID = '%s';""" % (transferUUID)
    accessionID=databaseInterface.queryAllSQL(sql)[0][0]
    if accessionID:
        eventIdentifierUUID = uuid.uuid4().__str__()
        eventOutcomeDetailNote =  "accession#" + MySQLdb.escape_string(accessionID) 
        insertIntoEvents(fileUUID=fileUUID, \
               eventIdentifierUUID=eventIdentifierUUID, \
               eventType="registration", \
               eventDateTime=date, \
               eventDetail="", \
               eventOutcome="", \
               eventOutcomeDetailNote=eventOutcomeDetailNote)
    
def addFileToSIP(filePathRelativeToSIP, fileUUID, sipUUID, taskUUID, date, sourceType="ingestion", use="original"):
    insertIntoFiles(fileUUID, filePathRelativeToSIP, date, sipUUID=sipUUID, use=use)
    insertIntoEvents(fileUUID=fileUUID, \
                   eventIdentifierUUID=taskUUID, \
                   eventType=sourceType, \
                   eventDateTime=date, \
                   eventDetail="", \
                   eventOutcome="", \
                   eventOutcomeDetailNote="")

#Used to write to file
#@output - the text to append to the file
#@fileName - The name of the file to create, or append to.
#@returns - 0 if ok, non zero if error occured.
def writeToFile(output, fileName, writeWhite=False):
    #print fileName
    if not writeWhite and output.isspace():
        return 0
    if fileName and output:
        #print "writing to: " + fileName
        if fileName.startswith("<^Not allowed to write to file^> "):
            return -1
        try:
            f = open(fileName, 'a')
            f.write(output.__str__())
            f.close()
            os.chmod(fileName, 488)
        except OSError, ose:
            print >>sys.stderr, "output Error", ose
            return -2
        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
            return -3
    else:
        print "No output, or file specified"
    return 0

def renameAsSudo(source, destination):
    """Used to move/rename Directories that the archivematica user may or may not have writes to move"""
    command = "sudo mv \"" + source + "\"   \"" + destination + "\""
    if isinstance(command, unicode):
        command = command.encode("utf-8")
    exitCode, stdOut, stdError = executeOrRun("command", command, "", printing=False)
    if exitCode:
        print >>sys.stderr, "exitCode:", exitCode
        print >>sys.stderr, stdOut
        print >>sys.stderr, stdError
        exit(exitCode)


def updateDirectoryLocation(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith):
    srcDB = src.replace(unitPath, unitPathReplaceWith)
    if not srcDB.endswith("/") and srcDB != unitPathReplaceWith:
        srcDB += "/"
    dstDB = dst.replace(unitPath, unitPathReplaceWith)
    if not dstDB.endswith("/") and dstDB != unitPathReplaceWith:
        dstDB += "/"
    sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND Files.currentLocation LIKE '" + MySQLdb.escape_string(srcDB) + "%' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        fileUUID = row[0]
        location = row[1]
        destDB = location.replace(srcDB, dstDB) 
        sql =  """UPDATE Files SET currentLocation='%s' WHERE fileUUID='%s';""" % (MySQLdb.escape_string(destDB), fileUUID)
        databaseInterface.runSQL(sql)
    if os.path.isdir(dst):
        if dst.endswith("/"):
            dst += "."
        else:
            dst += "/."
    print "moving: ", src, dst
    shutil.move(src, dst)

def updateFileLocation2(src, dst, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith):
    """Dest needs to be the actual full destination path with filename."""
    srcDB = src.replace(unitPath, unitPathReplaceWith)
    dstDB = dst.replace(unitPath, unitPathReplaceWith)
    # Fetch the file UUID
    sql = """SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND Files.currentLocation = '%s' AND %s = '%s';""" % (MySQLdb.escape_string(srcDB) , unitIdentifierType, unitIdentifier)
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) != 1:
        print >> sys.stderr, 'ERROR: file information not found:', len(rows), "rows for SQL:", sql
        print >> sys.stderr, 'Rows returned:', rows
        exit(4)
    # Move the file
    print "Moving", src, 'to', dst
    shutil.move(src, dst)
    # Update the DB
    for row in rows:
        fileUUID = row[0]
        sql =  """UPDATE Files SET currentLocation='%s' WHERE fileUUID='%s';""" % (MySQLdb.escape_string(dstDB), fileUUID)
        databaseInterface.runSQL(sql)

def updateFileLocation(src, dst, eventType, eventDateTime, eventDetail, eventIdentifierUUID = uuid.uuid4().__str__(), fileUUID="None", sipUUID = None, transferUUID=None, eventOutcomeDetailNote = ""):
    """If the file uuid is not provided, will use the sip uuid and old path to find the file uuid"""
    src = unicodeToStr(src)
    dst = unicodeToStr(dst)
    fileUUID = unicodeToStr(fileUUID)
    if not fileUUID or fileUUID == "None":
        sql = "Need to define transferUUID or sipUUID"
        if sipUUID:
            sql = "SELECT Files.fileUUID FROM Files WHERE removedTime = 0 AND Files.currentLocation = '" + MySQLdb.escape_string(src) + "' AND Files.sipUUID = '" + sipUUID + "';"
        elif transferUUID:
            sql = "SELECT Files.fileUUID FROM Files WHERE removedTime = 0 AND Files.currentLocation = '" + MySQLdb.escape_string(src) + "' AND Files.transferUUID = '" + transferUUID + "';"
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            fileUUID = unicodeToStr(row[0])
            row = c.fetchone()
        sqlLock.release()

    if eventOutcomeDetailNote == "":
        eventOutcomeDetailNote = "Original name=\"%s\"; cleaned up name=\"%s\"" %(src, dst)
        #eventOutcomeDetailNote = eventOutcomeDetailNote.decode('utf-8')
    #CREATE THE EVENT
    if not fileUUID:
        print >>sys.stderr, "Unable to find file uuid for: ", src, " -> ", dst
        exit(6)
    insertIntoEvents(fileUUID=fileUUID, eventIdentifierUUID=eventIdentifierUUID, eventType=eventType, eventDateTime=eventDateTime, eventDetail=eventDetail, eventOutcome="", eventOutcomeDetailNote=eventOutcomeDetailNote)

    #UPDATE THE CURRENT FILE PATH
    sql =  """UPDATE Files SET currentLocation='%s' WHERE fileUUID='%s';""" % (MySQLdb.escape_string(dst), fileUUID)
    databaseInterface.runSQL(sql)

def getFileUUIDLike(filePath, unitPath, unitIdentifier, unitIdentifierType, unitPathReplaceWith):
    """Dest needs to be the actual full destination path with filename."""
    ret = {}
    srcDB = filePath.replace(unitPath, unitPathReplaceWith)
    sql = "SELECT Files.fileUUID, Files.currentLocation FROM Files WHERE removedTime = 0 AND Files.currentLocation LIKE '" + MySQLdb.escape_string(srcDB) + "' AND " + unitIdentifierType + " = '" + unitIdentifier + "';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        ret[row[1]] = row[0]
    return ret
    
def updateFileGrpUsefileGrpUUID(fileUUID, fileGrpUse, fileGrpUUID):
    sql = "UPDATE Files SET fileGrpUse= '%s', fileGrpUUID= '%s' WHERE fileUUID = '%s';" % (fileGrpUse, fileGrpUUID, fileUUID)
    rows = databaseInterface.runSQL(sql)

def updateFileGrpUse(fileUUID, fileGrpUse):
    sql = "UPDATE Files SET fileGrpUse= '%s' WHERE fileUUID = '%s';" % (fileGrpUse, fileUUID)
    rows = databaseInterface.runSQL(sql)

def findFileInNormalizatonCSV(csv_path, commandClassification, target_file):
    """ Returns the original filename or None for a manually normalized file.

    csv_path: absolute path to normalization.csv
    commandClassification: "access" or "preservation"
    target_file: access or preservation file to match against

    TODO handle sanitized filenames
    """
    with open(csv_path, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        # Search CSV for an access/preservation filename that matches target_file

        # # Get original name of access file, to handle sanitized names
        # target_file = os.path.basename(opts.filePath)
        # sql = """SELECT Files.originalLocation FROM Files WHERE removedTime = 0 AND fileGrpUse='manualNormalization' AND Files.currentLocation LIKE '%{filename}' AND {unitIdentifierType} = '{unitIdentifier}';""".format(
        #     filename=target_file, unitIdentifierType=unitIdentifierType, unitIdentifier=unitIdentifier)
        # rows = databaseInterface.queryAllSQL(sql)
        # if len(rows) != 1:
        #     print >>sys.stderr, "Access file ({0}) not found in DB.".format(target_file)
        #     exit(2)
        # target_file = os.path.basename(rows[0][0])
        try:
            for row in reader:
                if "#" in row[0]:  # ignore comments
                    continue
                original, access, preservation = row
                if commandClassification == "access" and access.lower() == target_file.lower():
                    print "Found access file ({0}) for original ({1})".format(access, original)
                    return original
                if commandClassification == "preservation" and preservation.lower() == target_file.lower():
                    print "Found preservation file ({0}) for original ({1})".format(preservation, original)
                    return original
            else:
                return None
        except csv.Error as e:
            print >>sys.stderr, "Error reading {filename} on line {linenum}".format(
                filename=csv_path, linenum=reader.line_num)
            exit(2)
