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
import os
import sys
import databaseInterface
import MySQLdb
import uuid
from archivematicaFunctions import unicodeToStr

def insertIntoFiles(fileUUID, filePath, enteredSystem=databaseInterface.getUTCDate(), transferUUID="", sipUUID="", use="original"):
    if transferUUID != "" and sipUUID == "":
        databaseInterface.runSQL("""INSERT INTO Files (fileUUID, originalLocation, currentLocation, enteredSystem, fileGrpUse, transferUUID) VALUES (%s, %s, %s, %s, %s, %s)""",
            (fileUUID, filePath, filePath, enteredSystem, use, transferUUID)
        )
    elif transferUUID == "" and sipUUID != "":
        databaseInterface.runSQL("""INSERT INTO Files (fileUUID, originalLocation, currentLocation, enteredSystem, fileGrpUse, sipUUID) VALUES (%s, %s, %s, %s, %s, %s)""",
            (fileUUID, filePath, filePath, enteredSystem, use, sipUUID)
        )
    else:
        print >>sys.stderr, "not supported yet - both SIP and transfer UUID's defined (or neither defined)"
        print >>sys.stderr, "SIP UUID:", sipUUID
        print >>sys.stderr, "transferUUID:", transferUUID
        raise Exception("not supported yet - both SIP and transfer UUID's defined (or neither defined)", sipUUID + "-" + transferUUID)

def getAgentForFileUUID(fileUUID):
    agent = None
    if fileUUID == 'None':
        error_message = "Unable to get agent for file: no file UUID provided."
        print >>sys.stderr, error_message
        raise Exception(error_message)
    else:
        rows = databaseInterface.queryAllSQL("""SELECT sipUUID, transferUUID FROM Files WHERE fileUUID = %s;""", (fileUUID,))
        sipUUID, transferUUID = rows[0]
        if sipUUID:
            rows = databaseInterface.queryAllSQL("""SELECT variableValue FROM UnitVariables WHERE unitType = %s AND unitUUID = %s AND variable =%s;""", ('SIP', sipUUID, "activeAgent"))
            if len(rows):
                agent = "%s" % (rows[0])
        if transferUUID and not agent: #agent hasn't been found yet
            rows = databaseInterface.queryAllSQL("""SELECT variableValue FROM UnitVariables WHERE unitType = '%s' AND unitUUID = '%s' AND variable = '%s';""" % ("Transfer", transferUUID, "activeAgent"))
            if len(rows):
                agent = "%s" % (rows[0])
    return agent

def insertIntoEvents(fileUUID="", eventIdentifierUUID="", eventType="", eventDateTime=databaseInterface.getUTCDate(), eventDetail="", eventOutcome="", eventOutcomeDetailNote=""):
    agent = getAgentForFileUUID(fileUUID)
    if not agent:
        agent = 'NULL'
    if eventIdentifierUUID == "":
        eventIdentifierUUID = uuid.uuid4().__str__()
    databaseInterface.runSQL("""INSERT INTO Events (fileUUID, eventIdentifierUUID, eventType, eventDateTime, eventDetail, eventOutcome, eventOutcomeDetailNote, linkingAgentIdentifier)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (fileUUID, eventIdentifierUUID, eventType, eventDateTime,
         eventDetail, eventOutcome, eventOutcomeDetailNote, agent)
    )

def insertIntoDerivations(sourceFileUUID="", derivedFileUUID="", relatedEventUUID=""):
    databaseInterface.runSQL("""INSERT INTO Derivations
        (sourceFileUUID, derivedFileUUID, relatedEventUUID)
        VALUES (%s, %s, %s)""",
        (sourceFileUUID, derivedFileUUID, relatedEventUUID)
    )

def insertIntoFPCommandOutput(fileUUID="", fitsXMLString="", ruleUUID=""):
    databaseInterface.runSQL("""INSERT INTO FPCommandOutput
        (fileUUID, content, ruleUUID)
        VALUES (%s, %s, %s)""",
        (fileUUID, fitsXMLString, ruleUUID)
    )

def insertIntoFilesIDs(fileUUID="", formatName="", formatVersion="", formatRegistryName="", formatRegistryKey=""):
    databaseInterface.runSQL("""INSERT INTO FilesIDs
        (fileUUID, formatName, formatVersion, formatRegistryName, formatRegistryKey)
        VALUES (%s, %s, %s, %s, %s)""",
        (fileUUID, formatName, formatVersion,
         formatRegistryName, formatRegistryKey)
    )


#user approved?
#client connected/disconnected.

def logTaskCreatedSQL(taskManager, commandReplacementDic, taskUUID, arguments):
    taskUUID = taskUUID
    jobUUID = taskManager.jobChainLink.UUID
    fileUUID = ""
    if "%fileUUID%" in commandReplacementDic:
        fileUUID = commandReplacementDic["%fileUUID%"]
    taskexec = taskManager.execute
    fileName = os.path.basename(os.path.abspath(commandReplacementDic["%relativeLocation%"]))

    databaseInterface.runSQL("""INSERT INTO Tasks (taskUUID, jobUUID, fileUUID, fileName, exec, arguments, createdTime)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (taskUUID, jobUUID, fileUUID, fileName,
         taskexec, arguments, databaseInterface.getUTCDate())
    )

def logTaskAssignedSQL(taskUUID, client, date):
    databaseInterface.runSQL(
        """UPDATE Tasks SET startTime=%s, client=%s WHERE taskUUID=%s;""",
        (date, client, taskUUID)
    )

def logTaskCompletedSQL(task):
    print "Logging task output to db", task.UUID
    taskUUID = task.UUID.__str__()
    exitCode = task.results["exitCode"].__str__()
    stdOut = task.results["stdOut"]
    stdError = task.results["stdError"]

    databaseInterface.runSQL(
        """UPDATE Tasks SET endTime=%s, exitCode=%s, stdOut=%s, stdError=%s
           WHERE taskUUID=%s""",
        (databaseInterface.getUTCDate(), exitCode, stdOut, stdError, taskUUID)
    )

def logJobCreatedSQL(job):
    separator = databaseInterface.getSeparator()
    unitUUID =  job.unit.UUID
    decDate = databaseInterface.getDeciDate("." + job.createdDate.split(".")[-1])
    if job.unit.owningUnit != None:
        unitUUID = job.unit.owningUnit.UUID 
    databaseInterface.runSQL("""INSERT INTO Jobs (jobUUID, jobType, directory, SIPUUID, currentStep, unitType, microserviceGroup, createdTime, createdTimeDec, MicroServiceChainLinksPK, subJobOf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (job.UUID, job.description, job.unit.currentPath, unitUUID,
         "Executing command(s)", job.unit.__class__.__name__,
         str(job.microserviceGroup), job.createdDate, decDate, str(job.pk),
         str(job.subJobOf))
    )
    #TODO -un hardcode executing exeCommand

def logJobStepCompletedSQL(job):
    databaseInterface.runSQL("""INSERT INTO jobStepCompleted (jobUUID, step, completedTime)
        VALUES (%s, %s, %s)""",
        (job.UUID, job.step, databaseInterface.getUTCDate())
    )

def fileWasRemoved(fileUUID, utcDate=databaseInterface.getUTCDate(), eventDetail = "", eventOutcomeDetailNote = "", eventOutcome=""):
    eventIdentifierUUID = uuid.uuid4().__str__()
    eventType = "file removed"
    eventDateTime = utcDate
    insertIntoEvents(fileUUID=fileUUID, \
                       eventIdentifierUUID=eventIdentifierUUID, \
                       eventType=eventType, \
                       eventDateTime=eventDateTime, \
                       eventDetail=eventDetail, \
                       eventOutcome=eventOutcome, \
                       eventOutcomeDetailNote=eventOutcomeDetailNote)

    databaseInterface.runSQL(
        """UPDATE Files SET removedTime=%s, currentLocation=NULL WHERE fileUUID=%s""",
        (utcDate, fileUUID)
    )

def createSIP(path, UUID=None, sip_type='SIP'):
    if UUID is None:
        UUID = str(uuid.uuid4())
    print "Creating SIP:", UUID, "-", path
    sql = """INSERT INTO SIPs (sipUUID, currentPath, sipType)
        VALUES (%s, %s, %s)"""
    databaseInterface.runSQL(sql, (UUID, path, sip_type))
    return UUID

def deUnicode(str):
    if str == None:
        return None
    return unicode(str).encode('utf-8')
