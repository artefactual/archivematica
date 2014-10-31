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

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import Derivation, Event, File, FPCommandOutput, Job, SIP, Task, UnitVariable

def insertIntoFiles(fileUUID, filePath, enteredSystem=databaseInterface.getUTCDate(), transferUUID="", sipUUID="", use="original"):
    kwargs = {
        "uuid": fileUUID,
        "originallocation": filePath,
        "currentlocation": filePath,
        "enteredsystem": enteredSystem,
        "filegrpuse": use
    }
    if transferUUID != "" and sipUUID == "":
        kwargs["transfer_id"] = transferUUID
    elif transferUUID == "" and sipUUID != "":
        kwargs["sip_id"] = sipUUID
    else:
        print >>sys.stderr, "not supported yet - both SIP and transfer UUID's defined (or neither defined)"
        print >>sys.stderr, "SIP UUID:", sipUUID
        print >>sys.stderr, "transferUUID:", transferUUID
        raise Exception("not supported yet - both SIP and transfer UUID's defined (or neither defined)", sipUUID + "-" + transferUUID)

    File.objects.create(**kwargs)

def getAgentForFileUUID(fileUUID):
    agent = None
    if fileUUID == 'None':
        error_message = "Unable to get agent for file: no file UUID provided."
        print >>sys.stderr, error_message
        raise Exception(error_message)
    else:
        try:
            f = File.objects.get(uuid=fileUUID)
        except File.DoesNotExist:
            return

        if f.sip:
            try:
                var = UnitVariable.objects.get(unittype='SIP', unituuid=f.sip_id,
                                               variable='activeAgent')
                agent = var.variablevalue
            except UnitVariable.DoesNotExist:
                pass
        if f.transfer and agent is None: # agent hasn't been found yet
            try:
                var = UnitVariable.objects.get(unittype='Transfer',
                                               unituuid=f.transfer_id,
                                               variable='activeAgent')
                agent = var.variablevalue
            except UnitVariable.DoesNotExist:
                pass
    return agent

def insertIntoEvents(fileUUID="", eventIdentifierUUID="", eventType="", eventDateTime=databaseInterface.getUTCDate(), eventDetail="", eventOutcome="", eventOutcomeDetailNote=""):
    agent = getAgentForFileUUID(fileUUID)
    if not eventIdentifierUUID:
        eventIdentifierUUID = str(uuid.uuid4())

    Event.objects.create(event_id=eventIdentifierUUID, file_uuid_id=fileUUID,
                         event_type=eventType, event_datetime=eventDateTime,
                         event_detail=eventDetail, event_outcome=eventOutcome,
                         event_outcome_detail=eventOutcomeDetailNote,
                         linking_agent_id=agent)

def insertIntoDerivations(sourceFileUUID="", derivedFileUUID="", relatedEventUUID=""):
    if not sourceFileUUID:
        raise ValueError("sourceFileUUID must be specified")
    if not derivedFileUUID:
        raise ValueError("derivedFileUUID must be specified")

    Derivation.objects.create(source_file_id=sourceFileUUID,
                              derived_file_id=derivedFileUUID,
                              event_id=relatedEventUUID)

def insertIntoFPCommandOutput(fileUUID="", fitsXMLString="", ruleUUID=""):
    FPCommandOutput.objects.create(file_id=fileUUID, content=fitsXMLString,
                                   rule_id=ruleUUID)

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

    Task.objects.create(taskuuid=taskUUID,
                        job_id=jobUUID,
                        fileuuid=fileUUID,
                        filename=fileName,
                        execution=taskexec,
                        arguments=arguments,
                        createdtime=databaseInterface.getUTCDate())

def logTaskCompletedSQL(task):
    print "Logging task output to db", task.UUID
    taskUUID = task.UUID.__str__()
    exitCode = task.results["exitCode"].__str__()
    stdOut = task.results["stdOut"]
    stdError = task.results["stdError"]

    task = Task.objects.get(taskuuid=taskUUID)
    task.endtime = databaseInterface.getUTCDate()
    task.exitcode = exitCode
    task.stdout = stdOut
    task.stderror = stdError
    task.save()

def logJobCreatedSQL(job):
    separator = databaseInterface.getSeparator()
    unitUUID =  job.unit.UUID
    decDate = databaseInterface.getDeciDate("." + job.createdDate.split(".")[-1])
    if job.unit.owningUnit != None:
        unitUUID = job.unit.owningUnit.UUID 
    Job.objects.create(jobuuid=job.UUID,
                       jobtype=job.description,
                       directory=job.unit.currentPath,
                       sipuuid=unitUUID,
                       currentstep="Executing command(s)",
                       unittype=job.unit.__class__.__name__,
                       microservicegroup=str(job.microserviceGroup),
                       createdtime=job.createdDate,
                       createdtimedec=decDate,
                       microservicechainlink_id=str(job.pk),
                       subjobof=str(job.subJobOf))

    # TODO -un hardcode executing exeCommand

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

    f = File.objects.get(uuid=fileUUID)
    f.removedtime = utcDate
    f.currentlocation = None
    f.save()

def createSIP(path, UUID=None, sip_type='SIP'):
    if UUID is None:
        UUID = str(uuid.uuid4())
    print "Creating SIP:", UUID, "-", path
    sip = SIP(uuid=UUID,
              currentpath=path,
              sip_type=sip_type)
    sip.save()

    return UUID

def deUnicode(str):
    if str == None:
        return None
    return unicode(str).encode('utf-8')
