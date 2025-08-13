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
import datetime
import logging
import os
import sys
import uuid
from dataclasses import dataclass

from django.db.models import Min
from django.db.models import Q
from django.utils import timezone

from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Agent
from archivematica.dashboard.main.models import Derivation
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import FPCommandOutput
from archivematica.dashboard.main.models import Identifier
from archivematica.dashboard.main.models import Transfer

LOGGER = logging.getLogger("archivematica.common")


def insertIntoFiles(
    fileUUID,
    filePath,
    enteredSystem=None,
    transferUUID="",
    sipUUID="",
    use="original",
    originalLocation=None,
):
    """
    Creates a new entry in the Files table using the supplied arguments.

    :param str fileUUID:
    :param str filePath: The current path of the file on disk. Can contain variables; see the documentation for ReplacementDict for supported names.
    :param datetime enteredSystem: Timestamp for the event of file ingestion. Defaults to the current timestamp when the record is created.
    :param str transferUUID: UUID for the transfer containing this file. Can be empty. At least one of transferUUID or sipUUID must be defined. Mutually exclusive with sipUUID.
    :param str sipUUID: UUID for the SIP containing this file. Can be empty. At least one of transferUUID or sipUUID must be defined. Mutually exclusive with transferUUID.
    :param str use: A category used to group the file with others of the same kind. Will be included in the AIP's METS document in the USE attribute. Defaults to "original".
    :param str originalLocation: where the original location of the file needs to be recorded, such as premis:OriginalName fields, it can be set using this parameter here.

    :returns: None
    """
    if enteredSystem is None:
        enteredSystem = timezone.now()

    if not originalLocation:
        originalLocation = filePath

    kwargs = {
        "uuid": str(fileUUID),
        "originallocation": originalLocation.encode(),
        "currentlocation": filePath.encode(),
        "enteredsystem": enteredSystem,
        "filegrpuse": use,
    }
    if transferUUID != "" and sipUUID == "":
        kwargs["transfer_id"] = str(transferUUID)
    elif transferUUID == "" and sipUUID != "":
        kwargs["sip_id"] = str(sipUUID)
    else:
        print(
            "not supported yet - both SIP and transfer UUID's defined (or neither defined)",
            file=sys.stderr,
        )
        print("SIP UUID:", sipUUID, file=sys.stderr)
        print("transferUUID:", transferUUID, file=sys.stderr)
        raise Exception(
            "not supported yet - both SIP and transfer UUID's defined (or neither defined)",
            sipUUID + "-" + transferUUID,
        )

    return File.objects.create(**kwargs)


def getAMAgentsForFile(fileUUID):
    """
    Fetches the IDs for the Archivematica agents associated with the given file.

    The current user may be an Agent.
    The current user's agent ID is stored in a UnitVariable with the name "activeAgent", associated with either the SIP or the transfer containing the file.
    This function will attempt to fetch the unit variable from a SIP first,
    then the transfer.

    :returns: A list of Agent IDs
    """
    try:
        f = File.objects.get(uuid=fileUUID)
    except File.DoesNotExist:
        LOGGER.warning(
            "File with UUID %s does not exist in database; unable to fetch Agents",
            fileUUID,
        )
        return []

    # Fetch Agent for the User
    if f.sip:
        return f.sip.agents.values_list("pk", flat=True)
    elif f.transfer:
        return f.transfer.agents.values_list("pk", flat=True)

    # Fetch the default Agents
    return Agent.objects.filter(
        Agent.objects.default_agents_query_keywords()
    ).values_list("pk", flat=True)


def insertIntoEvents(
    fileUUID,
    eventIdentifierUUID="",
    eventType="",
    eventDateTime=None,
    eventDetail="",
    eventOutcome="",
    eventOutcomeDetailNote="",
    agents=None,
):
    """Creates a new entry in the Events table using the supplied arguments.

    :param str fileUUID: The UUID of the file with which this event is
        associated. Must point to a valid File UUID.
    :param str eventIdentifierUUID: The UUID for the event being generated. If
        not provided, a new UUID will be calculated using the version 4 scheme.
    :param str eventType: Can be blank.
    :param datetime eventDateTime: The time at which the event occurred. If not
        provided, the current date will be used.
    :param str eventDetail: Can be blank. Will be used in the eventDetail
        element in the AIP METS.
    :param str eventOutcome: Can be blank. Will be used in the eventOutcome
        element in the AIP METS.
    :param str eventOutcomeDetailNote: Can be blank. Will be used in the
        eventOutcomeDetailNote element in the AIP METS.
    :param list agents: List of Agent IDs to associate with this. If None
        provided, automatically fetches Agents representing Archivematica.
    :returns Event: The created event object.
    """
    if eventDateTime is None:
        eventDateTime = timezone.now()

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
        event_outcome_detail=eventOutcomeDetailNote,
    )
    # Splat agents list into multiple arguments
    event.agents.add(*agents)
    return event


def insertIntoDerivations(sourceFileUUID, derivedFileUUID, relatedEventUUID=None):
    """Creates a new entry in the Derivations table using the supplied
    arguments. The two files in this relationship should already exist in the
    Files table.

    :param str sourceFileUUID: The UUID of the original file.
    :param str derivedFileUUID: The UUID of the derived file.
    :param str relatedEventUUID: The UUID for an event describing the creation of the derived file. Can be blank.
    """
    if not sourceFileUUID:
        raise ValueError("sourceFileUUID must be specified")
    if not derivedFileUUID:
        raise ValueError("derivedFileUUID must be specified")

    Derivation.objects.create(
        source_file_id=sourceFileUUID,
        derived_file_id=derivedFileUUID,
        event_id=relatedEventUUID,
    )


def insertIntoFPCommandOutput(fileUUID="", fitsXMLString="", ruleUUID=""):
    """
    Creates a new entry in the FPCommandOutput table using the supplied argument.
    This is typically used to store output of file characterization.
    This data is intended to be unique per combination of fileUUID and ruleUUID; an exception will be raised if FPCommandOutput data already exists for a file with this ruleUUID.

    :param str fileUUID:
    :param str fitsXMLString: An XML document, encoded into a string. The name is historical; this can represent XML output from any software.
    :param str ruleUUID: The UUID of the FPR rule used to generate this XML data. Foreign key to FPRule.
    """
    FPCommandOutput.objects.create(
        file_id=fileUUID, content=fitsXMLString, rule_id=ruleUUID
    )


def fileWasRemoved(
    fileUUID, utcDate=None, eventDetail="", eventOutcomeDetailNote="", eventOutcome=""
):
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
        utcDate = timezone.now()

    eventIdentifierUUID = uuid.uuid4().__str__()
    eventType = "file removed"
    eventDateTime = utcDate
    insertIntoEvents(
        fileUUID=fileUUID,
        eventIdentifierUUID=eventIdentifierUUID,
        eventType=eventType,
        eventDateTime=eventDateTime,
        eventDetail=eventDetail,
        eventOutcome=eventOutcome,
        eventOutcomeDetailNote=eventOutcomeDetailNote,
    )

    f = File.objects.get(uuid=fileUUID)
    f.removedtime = utcDate
    f.currentlocation = None
    f.save()


def createSIP(path, UUID=None, sip_type="SIP", diruuids=False, printfn=print):
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
    printfn("Creating SIP:", UUID, "-", path)
    sip = SIP(uuid=UUID, currentpath=path, sip_type=sip_type, diruuids=diruuids)
    sip.save()

    return UUID


def deUnicode(unicode_string):
    """
    Convert a unicode string into an str by encoding it using UTF-8.

    :param unicode: A string. If not already a unicode string, it will be converted to one before encoding.
    :returns str: A UTF-8 encoded string, or None if the provided string was None. May be identical to the original string, if the original string contained only ASCII values.
    """
    if unicode_string is None:
        return None
    return str(unicode_string).encode("utf-8")


def get_transfer_details(transfer_uuid):
    transfer_name, accession_id, ingest_date = "", "", str(datetime.date.today())
    try:
        transfer = Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        pass
    else:
        transfer_name = transfer.currentlocation.split("/")[-2]
        if transfer.accessionid:
            accession_id = transfer.accessionid
        # It doesn't seem that Archivematica records the ingestion date
        # associated with the Transfer but we can look at the earliest file
        # entry instead - as long as there is a match which may not always be
        # the case.
        dt = File.objects.filter(transfer=transfer).aggregate(Min("enteredsystem"))[
            "enteredsystem__min"
        ]
        if dt:
            ingest_date = str(dt.date())

    return transfer_name, accession_id, ingest_date


def get_sip_identifiers(uuid):
    # Also index Directory identifiers so the AIP can be found through them
    return list(
        Identifier.objects.filter(Q(sip=uuid) | Q(directory__sip=uuid)).values_list(
            "value", flat=True
        )
    )


def _list_files_in_dir(path, filepaths=None):
    if filepaths is None:
        filepaths = []

    # Define entries
    for file in os.listdir(path):
        child_path = os.path.join(path, file)
        filepaths.append(child_path)

        # If entry is a directory, recurse
        if os.path.isdir(child_path) and os.access(child_path, os.R_OK):
            _list_files_in_dir(child_path, filepaths)

    # Return fully traversed data
    return filepaths


@dataclass
class TransferFileIndexData:
    file_paths: list[str]
    files_by_location: dict[str, File]
    bulk_extractor_reports: dict[str, list[str]]
    format_cache: dict[str, list[dict]]


def build_transfer_file_index_data(
    path: str, transfer_name: str, uuid: str, printfn
) -> TransferFileIndexData:
    """Prepare file paths, database lookups, and bulk extractor cache for transfer files.

    :param path: Transfer path on disk
    :param transfer_name: Name of the transfer
    :param uuid: Transfer UUID
    :param printfn: Print function for logging
    :return: TransferFileIndexData containing file_paths, files_by_location, bulk_extractor_reports, format_cache
    """
    ignore_files = ["processingMCP.xml"]
    file_paths = []
    currentlocations_to_encode = []
    currentlocation_to_filepath = {}

    # Step 1: Single directory traversal - gather file paths and currentlocations
    for filepath in _list_files_in_dir(path):
        if not os.path.isfile(filepath):
            continue

        filename = os.path.basename(filepath)
        if filename in ignore_files:
            stripped_path = filepath.replace(path, transfer_name + "/")
            printfn(f"Skipping indexing {stripped_path}")
            continue

        # Compute currentlocation for database lookup
        currentlocation = "%transferDirectory%" + os.path.relpath(
            filepath, path
        ).removeprefix("data/")

        file_paths.append(filepath)
        currentlocations_to_encode.append(currentlocation.encode())
        currentlocation_to_filepath[currentlocation] = filepath

    # Step 2: Batch database query for all files with optimized joins
    if currentlocations_to_encode:
        file_records = File.objects.filter(
            currentlocation__in=currentlocations_to_encode, transfer_id=uuid
        ).prefetch_related(
            "fileformatversion_set__format_version",
            "fileformatversion_set__format_version__format__group",
        )

        # Create lookup map from currentlocation to File record
        files_by_location = {f.currentlocation.decode(): f for f in file_records}

    else:
        files_by_location = {}

    # Step 3 & 4: Single traversal for format cache and bulk extractor reports
    format_cache = {}
    bulk_extractor_reports: dict[str, list[str]] = {}
    logs_dir = os.path.join(path, "data", "logs")
    logs_dir_exists = os.path.isdir(logs_dir)

    for f in files_by_location.values():
        file_uuid = str(f.uuid)

        # Build format cache
        formats = []
        for format_version in f.fileformatversion_set.all():
            formats.append(
                {
                    "puid": format_version.format_version.pronom_id,
                    "format": format_version.format_version.description,
                    "group": format_version.format_version.format.group.description,
                }
            )
        format_cache[file_uuid] = formats

        # Build bulk extractor reports
        log_path = os.path.join(logs_dir, "bulk-" + file_uuid)
        if not file_uuid or not logs_dir_exists or not os.path.isdir(log_path):
            bulk_extractor_reports[file_uuid] = []
            continue

        reports = []
        for report in ["telephone", "ccn", "ccn_track2", "pii"]:
            report_path = os.path.join(log_path, report + ".txt")
            if os.path.isfile(report_path) and os.path.getsize(report_path) > 0:
                reports.append(report)

        bulk_extractor_reports[file_uuid] = reports

    return TransferFileIndexData(
        file_paths=file_paths,
        files_by_location=files_by_location,
        bulk_extractor_reports=bulk_extractor_reports,
        format_cache=format_cache,
    )
