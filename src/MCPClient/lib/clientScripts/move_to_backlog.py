#!/usr/bin/env python2

"""Index transfer, create BagIt and send to backlog.

The transfer is indexed in Elasticsearch and converted into a BagIt. Finally,
we request to Storage Service to copy the transfer in the backlog location.
The local copy is removed.

PREMIS events are created after this job runs as part of the workflow.
"""

import multiprocessing
import os
import pprint
import shutil
import uuid

import django

django.setup()
from django.conf import settings as mcpclient_settings
from django.db import transaction
from django.db.models import Q

from archivematicaFunctions import get_bag_size, get_setting
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoEvents
import elasticSearchFunctions
from main.models import Agent, File, UnitVariable
import storageService as storage_service

from bagit import make_bag
import metsrw


logger = get_script_logger("archivematica.mcp.client.move_to_backlog")


class StorageServiceCreateFileError(Exception):
    pass


def _create_file(
    transfer_id, current_location, relative_transfer_path, backlog, backlog_path, size
):
    """Store the transfer in the backlog location.

    Storage Service will copy the contents of the transfers.
    """
    try:
        new_file = storage_service.create_file(
            uuid=transfer_id,
            origin_location=current_location["resource_uri"],
            origin_path=relative_transfer_path,
            current_location=backlog["resource_uri"],
            current_path=backlog_path,
            package_type="transfer",  # TODO use constant from storage service
            size=size,
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


def _index_transfer(job, transfer_id, transfer_path, size):
    """Index the transfer and its files in Elasticsearch."""
    if "transfers" not in mcpclient_settings.SEARCH_ENABLED:
        logger.info("Skipping indexing:" " Transfers indexing is currently disabled.")
        return
    elasticSearchFunctions.setup_reading_from_conf(mcpclient_settings)
    client = elasticSearchFunctions.get_client()
    elasticSearchFunctions.index_transfer_and_files(
        client, transfer_id, transfer_path, size, printfn=job.pyprint
    )


def _create_bag(transfer_id, transfer_path):
    """Convert the transfer directory into a bag using bagit-python."""
    algorithm = get_setting(
        "checksum_type", mcpclient_settings.DEFAULT_CHECKSUM_ALGORITHM
    )
    return make_bag(
        transfer_path,
        processes=multiprocessing.cpu_count(),
        checksums=[algorithm],
        bag_info={"External-Identifier": transfer_id},
    )


def _premis_event_data(event_id, event_type, created_at, agents):
    """Create a PREMIS event.

    Returns:
        metsrw.plugins.premisrw.premis.PREMISEvent
    """
    premis_data = (
        "event",
        metsrw.plugins.premisrw.PREMIS_3_0_META,
        (
            "event_identifier",
            ("event_identifier_type", "UUID"),
            ("event_identifier_value", event_id),
        ),
        ("event_type", event_type),
        ("event_date_time", created_at),
    )
    for agent in agents:
        premis_data += (
            (
                "linking_agent_identifier",
                ("linking_agent_identifier_type", agent.identifiertype),
                ("linking_agent_identifier_value", agent.identifiervalue),
            ),
        )
    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, metsrw.plugins.premisrw.PREMIS_3_0_VERSION
    )


def _transfer_agents(transfer_id):
    """Return the agents associated to a transfer.

    This is similar to ``databaseFunctions.getAMAgentsForFile`` but it returns
    a ``QuerySet`` instead. TODO: move to model?
    """
    query = Q(identifiertype="repository code")
    try:
        var = UnitVariable.objects.get(
            unittype="Transfer", unituuid=transfer_id, variable="activeAgent"
        )
    except UnitVariable.DoesNotExist:
        pass
    else:
        query |= Q(id=var.variablevalue)
    return Agent.objects.filter(query)


def _record_backlog_event(transfer_id, transfer_path, created_at):
    """Record backlog event in both the database and the transfer METS."""
    mets_path = os.path.join(
        transfer_path, "metadata", "submissionDocumentation", "METS.xml"
    )
    mets = metsrw.METSDocument().fromfile(mets_path)

    # Run all_files once, convert into a dict for faster lookups.
    fsentries = {entry.file_uuid: entry for entry in mets.all_files()}

    # Assuming the same agents apply to all files.
    agents = _transfer_agents(transfer_id)

    for file_obj in File.objects.filter(transfer_id=transfer_id).iterator():
        try:
            fsentry = fsentries[file_obj.uuid]
        except KeyError:
            continue
        event_id, event_type = str(uuid.uuid4()), "placement in backlog"
        fsentry.add_premis_event(
            _premis_event_data(event_id, event_type, created_at, agents)
        )
        insertIntoEvents(
            fileUUID=file_obj.uuid,
            eventIdentifierUUID=event_id,
            eventType=event_type,
            eventDateTime=created_at,
            agents=agents,
        )

    mets.write(mets_path, pretty_print=True)


def main(job, transfer_id, transfer_path, created_at):
    current_location = storage_service.get_first_location(purpose="CP")
    backlog = storage_service.get_first_location(purpose="BL")

    logger.info("Creating events...")
    _record_backlog_event(transfer_id, transfer_path, created_at)

    logger.info("Creating bag...")
    bag = _create_bag(transfer_id, transfer_path)

    size = get_bag_size(bag, transfer_path)

    logger.info("Indexing the transfer...")
    _index_transfer(job, transfer_id, transfer_path, size)

    # Make Transfer path relative to Location
    shared_path = os.path.join(current_location["path"], "")
    relative_transfer_path = transfer_path.replace(shared_path, "")

    # TODO this should use the same value as
    # dashboard/src/components/filesystem_ajax/views.py DEFAULT_BACKLOG_PATH
    transfer_name = os.path.basename(transfer_path.rstrip("/"))
    backlog_path = os.path.join("originals", transfer_name)

    logger.info("Moving transfer to backlog...")
    try:
        new_file = _create_file(
            transfer_id,
            current_location,
            relative_transfer_path,
            backlog,
            backlog_path,
            size,
        )
    except StorageServiceCreateFileError as err:
        errmsg = "Moving to backlog failed: {}.".format(err)
        logger.warning(errmsg)
        raise Exception(errmsg + " See logs for more details.")
    logger.info("Transfer moved (%s).", pprint.pformat(new_file))

    logger.info("Deleting transfer from processing space (%s)...", transfer_path)
    shutil.rmtree(transfer_path)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                transfer_id = job.args[1]
                transfer_path = job.args[2]
                created_at = job.args[3]
                job.set_status(main(job, transfer_id, transfer_path, created_at))
