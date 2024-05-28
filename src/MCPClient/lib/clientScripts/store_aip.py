#!/usr/bin/env python
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
import argparse
import os
from pprint import pformat
from uuid import uuid4

import django

# storageService requires Django to be set up

django.setup()
import storageService as storage_service
from archivematicaFunctions import escape
from client import metrics

# archivematicaCommon
from custom_handlers import get_script_logger
from django.core.exceptions import ValidationError
from django.db import transaction
from main.models import Agent
from main.models import DublinCore
from main.models import Event
from main.models import UnitVariable
from metsrw.plugins import premisrw

logger = get_script_logger("archivematica.mcp.client.storeAIP")


class StorageServiceCreateFileError(Exception):
    pass


def _create_file(
    uuid,
    current_location,
    relative_aip_path,
    aip_destination_uri,
    current_path,
    package_type,
    aip_subtype,
    size,
    sip_type,
    related_package_uuid,
):
    try:
        new_file = storage_service.create_file(
            uuid=uuid,
            origin_location=current_location["resource_uri"],
            origin_path=relative_aip_path,
            current_location=aip_destination_uri,
            current_path=current_path,
            package_type=package_type,
            aip_subtype=aip_subtype,
            size=size,
            update="REIN" in sip_type,
            related_package_uuid=related_package_uuid,
            events=get_events_from_db(uuid),
            agents=get_agents_from_db(uuid),
        )
    except storage_service.Error as err:
        raise StorageServiceCreateFileError(err)
    if new_file is None:
        raise StorageServiceCreateFileError(
            "Value returned by Storage Service is unexpected"
        )
    if new_file.get("status") == "FAIL":
        raise StorageServiceCreateFileError(
            'Object returned by Storage Service has status "FAIL"'
        )
    return new_file


def store_aip(job, aip_destination_uri, aip_path, sip_uuid, sip_name, sip_type):
    """Stores an AIP with the storage service.

    aip_destination_uri = storage service destination URI, should be of purpose
        AIP Store (AS)
    aip_path = Full absolute path to the AIP's current location on the local
        filesystem
    sip_uuid = UUID of the SIP, which will become the UUID of the AIP
    sip_name = SIP name.  Not used directly, but part of the AIP name

    Example inputs:
    storeAIP.py
        "/api/v1/location/9c2b5bb7-abd6-477b-88e0-57107219dace/"
        "/var/archivematica/sharedDirectory/currentlyProcessing/ep6-0737708e-9b99-471a-b331-283e2244164f/ep6-0737708e-9b99-471a-b331-283e2244164f.7z"
        "0737708e-9b99-471a-b331-283e2244164f"
        "ep6"
    """

    # FIXME Assume current Location is the one set up by default until location
    # is passed in properly, or use Agent to make sure is correct CP
    current_location = storage_service.get_first_location(purpose="CP")

    # Make aip_path relative to the Location
    shared_path = os.path.join(current_location["path"], "")  # Ensure ends with /
    relative_aip_path = aip_path.replace(shared_path, "")

    # Get the package type: AIC or AIP
    if "SIP" in sip_type or "AIP" in sip_type:  # Also matches AIP-REIN
        package_type = "AIP"
    elif "AIC" in sip_type:  # Also matches AIC-REIN
        package_type = "AIC"
    elif "DIP" in sip_type:
        package_type = "DIP"
        # FIXME: This script assumes the DIP path doesn't end with a trailing
        # slash, but the mcp.watched_dir_handler of the MCPServer appends it to
        # the %SIPDirectory% replacement variable which populates the
        # aip_filename of this script.
        aip_path = aip_path.rstrip(os.path.sep)

    # Uncompressed directory AIPs must be terminated in a /,
    # otherwise the storage service will place the directory
    # inside another directory of the same name.
    current_path = os.path.basename(aip_path)
    if os.path.isdir(aip_path) and not aip_path.endswith("/"):
        relative_aip_path = relative_aip_path + "/"

    # DIPs cannot share the AIP UUID, as the storage service depends on
    # having a unique UUID; assign a new one before uploading.
    # TODO allow mapping the AIP UUID to the DIP UUID for retrieval.
    related_package_uuid = None
    if sip_type == "DIP":
        uuid = str(uuid4())
        job.pyprint(f"Checking if DIP {uuid} parent AIP has been created...")

        # Set related package UUID, so a relationship to the parent AIP can be
        # created if if AIP has been stored. If the AIP hasn't yet been stored
        # take note of the DIP's UUID so it the relationship can later be
        # created when the AIP is stored.
        try:
            storage_service.get_file_info(uuid=sip_uuid)[0]  # Check existence
            related_package_uuid = sip_uuid
            job.pyprint("Parent AIP exists so relationship can be created.")
        except IndexError:
            UnitVariable.objects.create(
                unittype="SIP",
                unituuid=sip_uuid,
                variable="relatedPackage",
                variablevalue=uuid,
            )
            job.pyprint(
                f"Noting DIP UUID {uuid} related to AIP so relationship can be created when AIP is stored."
            )
    else:
        uuid = sip_uuid
        try:
            related_package = UnitVariable.objects.get(
                unituuid=sip_uuid, variable="relatedPackage"
            )
        except (UnitVariable.DoesNotExist, ValidationError):
            pass
        else:
            related_package_uuid = related_package.variablevalue

    # If AIP is a directory, calculate size recursively
    if os.path.isdir(aip_path):
        size = 0
        for dirpath, _, filenames in os.walk(aip_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                size += os.path.getsize(file_path)
    else:
        size = os.path.getsize(aip_path)

    # Get the AIP subtype from any DC type attribute supplied by the user for
    # the AIP. If found, this will replace 'Archival Information Package' in
    # ``<mets:div TYPE='Archival Information Package'>`` in the pointer file.
    sip_metadata_uuid = "3e48343d-e2d2-4956-aaa3-b54d26eb9761"
    try:
        dc = DublinCore.objects.get(
            metadataappliestotype_id=sip_metadata_uuid, metadataappliestoidentifier=uuid
        )
    except (DublinCore.DoesNotExist, ValidationError):
        aip_subtype = "Archival Information Package"
    else:
        aip_subtype = dc.type

    # Store the AIP
    try:
        new_file = _create_file(
            uuid,
            current_location,
            relative_aip_path,
            aip_destination_uri,
            current_path,
            package_type,
            aip_subtype,
            size,
            sip_type,
            related_package_uuid,
        )
    except StorageServiceCreateFileError as err:
        errmsg = f"{sip_type} creation failed: {err}."
        logger.warning(errmsg)
        raise Exception(errmsg + " See logs for more details.")

    message = f"Storage Service created {sip_type}:\n{pformat(new_file)}"
    logger.info(message)
    job.pyprint(message)

    if "AIP" in package_type:
        metrics.aip_stored(sip_uuid, size)
    elif "DIP" in package_type:
        metrics.dip_stored(sip_uuid, size)

    return 0

    # FIXME this should be moved to the storage service and areas that rely
    # on the thumbnails should be updated

    # #copy thumbnails to an AIP-specific directory for easy admin access
    # thumbnailSourceDir = os.path.join(bag, 'data', 'thumbnails')
    # thumbnailDestDir   = os.path.join(destination['path'], 'thumbnails', sip_uuid)

    # #create thumbnail dest dir
    # if not os.path.exists(thumbnailDestDir):
    #     os.makedirs(thumbnailDestDir)

    # #copy thumbnails to destination directory
    # thumbnails = os.listdir(thumbnailSourceDir)
    # for filename in thumbnails:
    #     shutil.copy(os.path.join(thumbnailSourceDir, filename), thumbnailDestDir)


def get_events_from_db(uuid):
    events = []
    for event_mdl in Event.objects.filter(file_uuid_id=uuid):
        event = [
            "event",
            premisrw.PREMIS_3_0_META,
            (
                "event_identifier",
                ("event_identifier_type", "UUID"),
                ("event_identifier_value", str(event_mdl.event_id)),
            ),
            ("event_type", event_mdl.event_type),
            ("event_date_time", event_mdl.event_datetime.isoformat()),
            # String detailing the program and algorithm used and the program's
            # version (and any notable parameters passed).
            (
                "event_detail_information",
                ("event_detail", escape(event_mdl.event_detail)),
            ),
            (
                "event_outcome_information",
                ("event_outcome", event_mdl.event_outcome),
                (
                    "event_outcome_detail",
                    (
                        "event_outcome_detail_note",
                        escape(event_mdl.event_outcome_detail),
                    ),
                ),
            ),
        ]
        for agent_mdl in Agent.objects.extend_queryset_with_preservation_system(
            event_mdl.agents.all()
        ):
            event.append(
                (
                    "linking_agent_identifier",
                    ("linking_agent_identifier_type", agent_mdl.identifiertype),
                    ("linking_agent_identifier_value", agent_mdl.identifiervalue),
                )
            )
        events.append(tuple(event))
    return events


def get_agents_from_db(uuid):
    agents = []
    for agent_mdl in Agent.objects.extend_queryset_with_preservation_system(
        Agent.objects.filter(event__file_uuid_id=uuid).distinct()
    ):
        agents.append(
            (
                "agent",
                premisrw.PREMIS_3_0_META,
                (
                    "agent_identifier",
                    ("agent_identifier_type", agent_mdl.identifiertype),
                    ("agent_identifier_value", agent_mdl.identifiervalue),
                ),
                ("agent_name", agent_mdl.name),
                ("agent_type", agent_mdl.agenttype),
            )
        )
    return agents


def call(jobs):
    parser = argparse.ArgumentParser(description="Create AIP pointer file.")
    parser.add_argument("aip_destination_uri", type=str, help="%AIPsStore%")
    parser.add_argument("aip_filename", type=str, help="%AIPFilename%")
    parser.add_argument("sip_uuid", type=str, help="%SIPUUID%")
    parser.add_argument("sip_name", type=str, help="%SIPName%")
    parser.add_argument("sip_type", type=str, help="%SIPType%")

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])
                job.set_status(
                    store_aip(
                        job,
                        args.aip_destination_uri,
                        args.aip_filename,
                        args.sip_uuid,
                        args.sip_name,
                        args.sip_type,
                    )
                )
