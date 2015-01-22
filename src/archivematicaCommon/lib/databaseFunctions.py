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
from datetime import datetime
import os
import string
import sys
import uuid

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import Derivation, Event, File, FileID, FPCommandOutput, Job, SIP, Task, Transfer, UnitVariable

def getUTCDate():
    """Returns a string of the UTC date & time in ISO format"""
    d = datetime.utcnow()
    return d.isoformat('T')

def getDeciDate(date):
    valid = "." + string.digits
    ret = ""
    for c in date:
        if c in valid:
            ret += c
        #else:
            #ret += replacementChar
    return str("{:10.10f}".format(float(ret)))

def insertIntoFiles(fileUUID, filePath, enteredSystem=None, transferUUID="", sipUUID="", use="original"):
    """
    Creates a new entry in the Files table using the supplied arguments.

    :param str fileUUID:
    :param str filePath: The current path of the file on disk. Can contain variables; see the documentation for ReplacementDict for supported names.
    :param datetime.datetime enteredSystem: Timestamp for the event of file ingestion. Defaults to the current timestamp when the record is created.
    :param str transferUUID: UUID for the transfer containing this file. Can be empty. At least one of transferUUID or sipUUID must be defined. Mutually exclusive with sipUUID.
    :param str sipUUID: UUID for the SIP containing this file. Can be empty. At least one of transferUUID or sipUUID must be defined. Mutually exclusive with transferUUID.
    :param str use: A category used to group the file with others of the same kind. Will be included in the AIP's METS document in the USE attribute. Defaults to "original".

    :returns: None
    """
    if enteredSystem is None:
        enteredSystem = getUTCDate()

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
    """
    Fetches the ID for the agent associated with the given file, if one exists.

    The agent ID is stored in a UnitVariable with the name "activeAgent", associated with either the SIP or the transfer containing the file.
    This function will attempt to fetch the unit variable from a SIP first,
    then the transfer.

    The agent ID is the pk to a row in the Agent table.
    Note that this transfer does not actually verify that an agent with this pk exists, just that the value is contained in a UnitVariable associated with this SIP.

    :returns: The agent ID, as a string, or None if no agent could be found.
    """
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

def insertIntoEvents(fileUUID="", eventIdentifierUUID="", eventType="", eventDateTime=None, eventDetail="", eventOutcome="", eventOutcomeDetailNote=""):
    """
    Creates a new entry in the Events table using the supplied arguments.

    :param str fileUUID: The UUID of the file with which this event is associated. Can be blank.
    :param str eventIdentifierUUID: The UUID for the event being generated. If not provided, a new UUID will be calculated using the version 4 scheme.
    :param str eventType: Can be blank.
    :param datetime.datetime eventDateTime: The time at which the event occurred. If not provided, the current date will be used.
    :param str eventDetail: Can be blank. Will be used in the eventDetail element in the AIP METS.
    :param str eventOutcome: Can be blank. Will be used in the eventOutcome element in the AIP METS.
    :param str eventOutcomeDetailNote: Can be blank. Will be used in the eventOutcomeDetailNote element in the AIP METS.
    """
    if eventDateTime is None:
        eventDateTime = getUTCDate()

    agent = getAgentForFileUUID(fileUUID)
    if not eventIdentifierUUID:
        eventIdentifierUUID = str(uuid.uuid4())

    Event.objects.create(event_id=eventIdentifierUUID, file_uuid_id=fileUUID,
                         event_type=eventType, event_datetime=eventDateTime,
                         event_detail=eventDetail, event_outcome=eventOutcome,
                         event_outcome_detail=eventOutcomeDetailNote,
                         linking_agent_id=agent)

def insertIntoDerivations(sourceFileUUID="", derivedFileUUID="", relatedEventUUID=""):
    """
    Creates a new entry in the Derivations table using the supplied arguments. The two files in this relationship should already exist in the Files table.

    :param str sourceFileUUID: The UUID of the original file.
    :param str derivedFileUUID: The UUID of the derived file.
    :param str relatedEventUUID: The UUID for an event describing the creation of the derived file. Can be blank.
    """
    if not sourceFileUUID:
        raise ValueError("sourceFileUUID must be specified")
    if not derivedFileUUID:
        raise ValueError("derivedFileUUID must be specified")

    Derivation.objects.create(source_file_id=sourceFileUUID,
                              derived_file_id=derivedFileUUID,
                              event_id=relatedEventUUID)

def insertIntoFPCommandOutput(fileUUID="", fitsXMLString="", ruleUUID=""):
    """
    Creates a new entry in the FPCommandOutput table using the supplied argument.
    This is typically used to store output of file characterization.
    This data is intended to be unique per combination of fileUUID and ruleUUID; an exception will be raised if FPCommandOutput data already exists for a file with this ruleUUID.

    :param str fileUUID:
    :param str fitsXMLString: An XML document, encoded into a string. The name is historical; this can represent XML output from any software.
    :param str ruleUUID: The UUID of the FPR rule used to generate this XML data. Foreign key to FPRule.
    """
    FPCommandOutput.objects.create(file_id=fileUUID, content=fitsXMLString,
                                   rule_id=ruleUUID)

def insertIntoFilesIDs(fileUUID="", formatName="", formatVersion="", formatRegistryName="", formatRegistryKey=""):
    """
    Creates a new entry in the FilesIDs table using the provided data.
    This function, and its associated table, may be removed in the future.
    """
    f = FileID(file_id=fileUUID,
               format_name=formatName,
               format_version=formatVersion,
               format_registry_name=formatRegistryName,
               format_registry_key=formatRegistryKey)
    f.save()


#user approved?
#client connected/disconnected.

def logTaskCreatedSQL(taskManager, commandReplacementDic, taskUUID, arguments):
    """
    Creates a new entry in the Tasks table using the supplied data.

    :param MCPServer.linkTaskManager taskManager: A linkTaskManager subclass instance.
    :param ReplacementDict commandReplacementDic: A ReplacementDict or dict instance. %fileUUID% and %relativeLocation% variables will be looked up from this dict.
    :param str taskUUID: The UUID to be used for this Task in the database.
    :param str arguments: The arguments to be passed to the command when it is executed, as a string. Can contain replacement variables; see ReplacementDict for supported values.
    """
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
                        createdtime=getUTCDate())

def logTaskCompletedSQL(task):
    """
    Fetches execution data from the completed task and logs it to the database.
    Updates the entry in the Tasks table with data in the provided task.
    Saves the following fields: exitCode, stdOut, stdError

    :param task:
    """
    print "Logging task output to db", task.UUID
    taskUUID = task.UUID.__str__()
    exitCode = task.results["exitCode"].__str__()
    stdOut = task.results["stdOut"]
    stdError = task.results["stdError"]

    task = Task.objects.get(taskuuid=taskUUID)
    task.endtime = getUTCDate()
    task.exitcode = exitCode
    task.stdout = stdOut
    task.stderror = stdError
    task.save()

def logJobCreatedSQL(job):
    """
    Logs a job's properties into the Jobs table in the database.

    :param jobChainLink job: A jobChainLink instance.
    :returns None:    
    """
    unitUUID =  job.unit.UUID
    decDate = getDeciDate("." + job.createdDate.split(".")[-1])
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

def fileWasRemoved(fileUUID, utcDate=None, eventDetail = "", eventOutcomeDetailNote = "", eventOutcome=""):
    """
    Logs the removal of a file from the database.
    Updates the properties of the row in the Files table for the provided fileUUID, and logs the removal in the Events table with an event of type "file removed".

    :param str fileUUID:
    :param datetime.datetime utcDate: The date of the removal. Defaults to the current date.
    :param str eventDetail: The eventDetail for the logged event. Can be blank.
    :param str eventOutcomeDetailNote: The eventOutcomeDetailNote for the logged event. Can be blank.
    :param str eventOutcome: The eventOutcome for the logged event. Can be blank.
    """
    if utcDate is None:
        utcDate = getUTCDate()

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
    """
    Create a new SIP object for a SIP at the given path.

    :param str path: The current path of the SIP on disk. Can contain variables; see the documentation for ReplacementDict for supported names.
    :param str UUID: The UUID to be created for the SIP. If not specified, a new UUID will be generated using the version 4 scheme.
    :param str sip_type: A string representing the type of the SIP. Defaults to "SIP". The other value typically used is "AIC".

    :returns str: The UUID for the created SIP.
    """
    if UUID is None:
        UUID = str(uuid.uuid4())
    print "Creating SIP:", UUID, "-", path
    sip = SIP(uuid=UUID,
              currentpath=path,
              sip_type=sip_type)
    sip.save()

    return UUID

def getAccessionNumberFromTransfer(UUID):
    """
    Fetches the accession number from a transfer, given its UUID.

    :param str UUID: The UUID of the transfer, as a string.

    :returns str: The accession number, as a string.
    :raises ValueError: if the requested Transfer cannot be found.
    """

    try:
        return Transfer.objects.get(uuid=UUID).accessionid
    except Transfer.DoesNotExist:
        raise ValueError("No Transfer found for UUID: {}".format(UUID))


def deUnicode(str):
    """
    Convert a unicode string into an str by encoding it using UTF-8.

    :param unicode: A string. If not already a unicode string, it will be converted to one before encoding.
    :returns str: A UTF-8 encoded string, or None if the provided string was None. May be identical to the original string, if the original string contained only ASCII values.
    """
    if str == None:
        return None
    return unicode(str).encode('utf-8')
