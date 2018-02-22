#!/usr/bin/env python2

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
from __future__ import print_function

from functools import wraps
import logging
import os
import string
import sys
import uuid

from archivematicaFunctions import strToUnicode

from django.db import close_old_connections
from django.db.models import Q
from django.utils import timezone
from main.models import Agent, Derivation, Event, File, FPCommandOutput, Job, SIP, Task, Transfer, UnitVariable

LOGGER = logging.getLogger('archivematica.common')


def auto_close_db(f):
    """Decorator to ensure the db connection is closed when the function returns."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        finally:
            close_old_connections()
    return wrapper


def getUTCDate():
    """Returns a timezone-aware representation of the current datetime in UTC."""
    return timezone.now()


def getDeciDate(date):
    valid = "." + string.digits
    ret = ""
    for c in date:
        if c in valid:
            ret += c
        # else:
        #     ret += replacementChar
    return str("{:10.10f}".format(float(ret)))


def insertIntoFiles(fileUUID, filePath, enteredSystem=None, transferUUID="", sipUUID="", use="original"):
    """
    Creates a new entry in the Files table using the supplied arguments.

    :param str fileUUID:
    :param str filePath: The current path of the file on disk. Can contain variables; see the documentation for ReplacementDict for supported names.
    :param datetime enteredSystem: Timestamp for the event of file ingestion. Defaults to the current timestamp when the record is created.
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
        print("not supported yet - both SIP and transfer UUID's defined (or neither defined)", file=sys.stderr)
        print("SIP UUID:", sipUUID, file=sys.stderr)
        print("transferUUID:", transferUUID, file=sys.stderr)
        raise Exception("not supported yet - both SIP and transfer UUID's defined (or neither defined)", sipUUID + "-" + transferUUID)

    File.objects.create(**kwargs)


def getAMAgentsForFile(fileUUID):
    """
    Fetches the IDs for the Archivematica agents associated with the given file.

    The current user may be an Agent.
    The current user's agent ID is stored in a UnitVariable with the name "activeAgent", associated with either the SIP or the transfer containing the file.
    This function will attempt to fetch the unit variable from a SIP first,
    then the transfer.

    :returns: A list of Agent IDs
    """
    agents = []

    try:
        f = File.objects.get(uuid=fileUUID)
    except File.DoesNotExist:
        LOGGER.warning('File with UUID %s does not exist in database; unable to fetch Agents', fileUUID)
        return []

    # Fetch Agent for the User
    if f.sip:
        try:
            var = UnitVariable.objects.get(unittype='SIP', unituuid=f.sip_id,
                                           variable='activeAgent')
            agents.append(int(var.variablevalue))
        except UnitVariable.DoesNotExist:
            pass
    if f.transfer and not agents:  # agent hasn't been found yet
        try:
            var = UnitVariable.objects.get(unittype='Transfer',
                                           unituuid=f.transfer_id,
                                           variable='activeAgent')
            agents.append(int(var.variablevalue))
        except UnitVariable.DoesNotExist:
            pass
    # Fetch other Archivematica Agents
    am_agents = Agent.objects.filter(Q(identifiertype='repository code') | Q(identifiertype='preservation system')).values_list('pk', flat=True)
    agents.extend(am_agents)
    return agents


def insertIntoEvents(fileUUID, eventIdentifierUUID="", eventType="", eventDateTime=None, eventDetail="", eventOutcome="", eventOutcomeDetailNote="", agents=None):
    """
    Creates a new entry in the Events table using the supplied arguments.

    :param str fileUUID: The UUID of the file with which this event is associated. Must point to a valid File UUID.
    :param str eventIdentifierUUID: The UUID for the event being generated. If not provided, a new UUID will be calculated using the version 4 scheme.
    :param str eventType: Can be blank.
    :param datetime eventDateTime: The time at which the event occurred. If not provided, the current date will be used.
    :param str eventDetail: Can be blank. Will be used in the eventDetail element in the AIP METS.
    :param str eventOutcome: Can be blank. Will be used in the eventOutcome element in the AIP METS.
    :param str eventOutcomeDetailNote: Can be blank. Will be used in the eventOutcomeDetailNote element in the AIP METS.
    :param list agents: List of Agent IDs to associate with this. If None provided, automatically fetches Agents representing Archivematica.
    """
    if eventDateTime is None:
        eventDateTime = getUTCDate()

    # Assume the Agent is Archivematica & the current user
    if not agents:
        agents = getAMAgentsForFile(fileUUID)
    if not eventIdentifierUUID:
        eventIdentifierUUID = str(uuid.uuid4())

    event = Event.objects.create(
        event_id=eventIdentifierUUID,
        file_uuid_id=fileUUID,
        event_type=eventType,
        event_datetime=eventDateTime,
        event_detail=eventDetail,
        event_outcome=eventOutcome,
        event_outcome_detail=eventOutcomeDetailNote
    )
    # Splat agents list into multiple arguments
    event.agents.add(*agents)


def insertIntoDerivations(sourceFileUUID, derivedFileUUID, relatedEventUUID=None):
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


# user approved?
# client connected/disconnected.

def logTaskCreatedSQL(taskManager, commandReplacementDic, taskUUID, arguments):
    """
    Creates a new entry in the Tasks table using the supplied data.

    :param MCPServer.linkTaskManager taskManager: A linkTaskManager subclass instance.
    :param ReplacementDict commandReplacementDic: A ReplacementDict or dict instance. %fileUUID% and %relativeLocation% variables will be looked up from this dict.
    :param str taskUUID: The UUID to be used for this Task in the database.
    :param str arguments: The arguments to be passed to the command when it is executed, as a string. Can contain replacement variables; see ReplacementDict for supported values.
    """
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
    print("Logging task output to db", task.UUID)
    taskUUID = task.UUID.__str__()
    exitCode = task.results["exitCode"].__str__()
    stdOut = task.results["stdOut"]
    stdError = task.results["stdError"]

    task = Task.objects.get(taskuuid=taskUUID)
    task.endtime = getUTCDate()
    task.exitcode = exitCode
    # ``strToUnicode`` here prevents the MCP server from crashing when, e.g.,
    # stderr contains Latin-1-encoded chars such as \xa9, i.e., the copyright
    # symbol, cf. #9967.
    task.stdout = strToUnicode(stdOut, obstinate=True)
    task.stderror = strToUnicode(stdError, obstinate=True)
    task.save()


def logJobCreatedSQL(job):
    """
    Logs a job's properties into the Jobs table in the database.

    :param jobChainLink job: A jobChainLink instance.
    :returns None:
    """
    unitUUID = job.unit.UUID
    # microseconds are always 6 digits
    # The number returned may have a leading 0 which needs to be preserved
    decDate = getDeciDate("." + str(job.createdDate.microsecond).zfill(6))
    try:
        if job.unit.owningUnit is not None:
            unitUUID = job.unit.owningUnit.UUID
    except AttributeError:
        pass
    Job.objects.create(jobuuid=job.UUID,
                       jobtype=job.description,
                       directory=job.unit.currentPath,
                       sipuuid=unitUUID,
                       currentstep=Job.STATUS_EXECUTING_COMMANDS,
                       unittype=job.unit.__class__.__name__,
                       microservicegroup=str(job.microserviceGroup),
                       createdtime=job.createdDate,
                       createdtimedec=decDate,
                       microservicechainlink_id=str(job.pk))

    # TODO -un hardcode executing exeCommand


def fileWasRemoved(fileUUID, utcDate=None, eventDetail="", eventOutcomeDetailNote="", eventOutcome=""):
    """
    Logs the removal of a file from the database.
    Updates the properties of the row in the Files table for the provided fileUUID, and logs the removal in the Events table with an event of type "file removed".

    :param str fileUUID:
    :param datetime utcDate: The date of the removal. Defaults to the current date.
    :param str eventDetail: The eventDetail for the logged event. Can be blank.
    :param str eventOutcomeDetailNote: The eventOutcomeDetailNote for the logged event. Can be blank.
    :param str eventOutcome: The eventOutcome for the logged event. Can be blank.
    """
    if utcDate is None:
        utcDate = getUTCDate()

    eventIdentifierUUID = uuid.uuid4().__str__()
    eventType = "file removed"
    eventDateTime = utcDate
    insertIntoEvents(fileUUID=fileUUID,
                     eventIdentifierUUID=eventIdentifierUUID,
                     eventType=eventType,
                     eventDateTime=eventDateTime,
                     eventDetail=eventDetail,
                     eventOutcome=eventOutcome,
                     eventOutcomeDetailNote=eventOutcomeDetailNote)

    f = File.objects.get(uuid=fileUUID)
    f.removedtime = utcDate
    f.currentlocation = None
    f.save()


def createSIP(path, UUID=None, sip_type='SIP', diruuids=False):
    """
    Create a new SIP object for a SIP at the given path.

    :param str path: The current path of the SIP on disk. Can contain variables; see the documentation for ReplacementDict for supported names.
    :param str UUID: The UUID to be created for the SIP. If not specified, a new UUID will be generated using the version 4 scheme.
    :param str sip_type: A string representing the type of the SIP. Defaults to "SIP". The other value typically used is "AIC".
    :param str diruuids: A boolean indicating whether the SIP should have UUIDs assigned to all of its subdirectories. This param is relevant in filesystem_ajax/views.py and clientScripts/createSIPfromTransferObjects.py.

    :returns str: The UUID for the created SIP.
    """
    if UUID is None:
        UUID = str(uuid.uuid4())
    print("Creating SIP:", UUID, "-", path)
    sip = SIP(uuid=UUID,
              currentpath=path,
              sip_type=sip_type,
              diruuids=diruuids)
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
    if str is None:
        return None
    return unicode(str).encode('utf-8')
