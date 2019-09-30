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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

# ~DOC~
#
# --- This is the MCP (master control program) ---
# The intention of this program is to provide a centralized automated distributed system for performing an arbitrary set of tasks on a directory.
# Distributed in that the work can be performed on more than one physical computer simultaneously.
# Centralized in that there is one centre point for configuring flow through the system.
# Automated in that the tasks performed will be based on the config files and instantiated for each of the targets.
#
# It loads configurations from the database.
#
# stdlib, alphabetical by import source
import getpass
import logging
import logging.config
import os
import signal
import sys
import threading
import time

import django

django.setup()
from django.conf import settings as django_settings
from django.db.models import Q

# This project, alphabetical by import source
from utils import log_exceptions

import processing
from db import auto_close_old_connections
from job import JobChain
from package import DIP, Transfer, SIP
from scheduler import package_scheduler
from utils import valid_uuid
from watch_dirs import watch_directories
from workflow import load as load_workflow, SchemaValidationError
import metrics
import RPCServer

from archivematicaFunctions import unicodeToStr
from databaseFunctions import createSIP, getUTCDate
import dicts

from main import models

logger = logging.getLogger("archivematica.mcp.server")

# time to sleep to allow db to be updated with the new location of a SIP
dbWaitSleep = 2

# Tracks whether a sigkill has been received or not
shutdown_event = threading.Event()

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join(__file__))), "assets"
)

DEFAULT_WORKFLOW = os.path.join(ASSETS_DIR, "workflow.json")


def fetchUUIDFromPath(path):
    # find UUID on end of SIP path
    uuidLen = -36
    if valid_uuid(path[uuidLen - 1 : -1]):
        return path[uuidLen - 1 : -1]


@auto_close_old_connections
def findOrCreateSipInDB(path, waitSleep=dbWaitSleep, unit_type="SIP"):
    """Matches a directory to a database sip by it's appended UUID, or path. If it doesn't find one, it will create one"""
    path = path.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%", 1)

    query = Q(currentpath=path)

    # Find UUID on end of SIP path
    UUID = fetchUUIDFromPath(path)
    sip = None
    if UUID:
        query = query | Q(uuid=UUID)

    sips = models.SIP.objects.filter(query)
    count = sips.count()
    if count > 1:
        # This might have happened because the UUID at the end of the directory
        # name corresponds to a different SIP in the database.
        # Try refiltering the queryset on path alone, and see if that brought us
        # down to a single SIP.
        sips = sips.filter(currentpath=path)
        count = sips.count()

        # Darn: we must have multiple SIPs with the same path in the database.
        # We have no reasonable way to recover from this condition.
        if count > 1:
            logger.error(
                "More than one SIP for path %s and/or UUID %s, using first result",
                path,
                UUID,
            )
    if count > 0:
        sip = sips[0]
        UUID = sip.uuid
        logger.info("Using existing SIP %s at %s", UUID, path)
    else:
        logger.info("Not using existing SIP %s at %s", UUID, path)

    if sip is None:
        # Create it
        # Note that if UUID is None here, a new UUID will be generated
        # and returned by the function; otherwise it returns the
        # value that was passed in.
        UUID = createSIP(path, UUID=UUID)
        logger.info("Creating SIP %s at %s", UUID, path)
    else:
        current_path = sip.currentpath
        if current_path != path and unit_type == "SIP":
            # Ensure path provided matches path in DB
            sip.currentpath = path
            sip.save()

    return UUID


@log_exceptions
@auto_close_old_connections
def createUnitAndJobChain(path, watched_dir, workflow):
    path = unicodeToStr(path)
    if os.path.isdir(path):
        path = path + "/"
    logger.debug("Starting chain for %s", path)
    if not os.path.exists(path):
        return
    unit = None
    unit_type = watched_dir["unit_type"]
    if os.path.isdir(path):
        if unit_type == "SIP":
            UUID = findOrCreateSipInDB(path)
            unit = SIP(path, UUID)
        elif unit_type == "DIP":
            UUID = findOrCreateSipInDB(path, unit_type="DIP")
            unit = DIP(path, UUID)
        elif unit_type == "Transfer":
            UUID = fetchUUIDFromPath(path)
            unit = Transfer(path, UUID)
    elif os.path.isfile(path):
        if unit_type == "Transfer":
            unit = Transfer(path, None)
    else:
        return
    job_chain = JobChain(unit, watched_dir.chain, workflow)
    package_scheduler.schedule_job_chain(job_chain)


def signal_handler(signalReceived, frame):
    """Used to handle the stop/kill command signals (SIGKILL)"""
    logger.info("Recieved signal %s in frame %s", signalReceived, frame)
    shutdown_event.set()
    threads = threading.enumerate()
    for thread in threads:
        logger.warning("Not stopping %s %s", type(thread), thread)
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)
    exit(0)


@log_exceptions
def debugMonitor():
    """Periodically prints out status of MCP, including whether the database lock is locked, thread count, etc."""
    while not shutdown_event.is_set():
        logger.debug("Debug monitor: datetime: %s", getUTCDate())
        logger.debug("Debug monitor: thread count: %s", threading.activeCount())
        time.sleep(3600)


@log_exceptions
def flushOutputs():
    while not shutdown_event.is_set():
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)


@auto_close_old_connections
def cleanupOldDbEntriesOnNewRun():
    models.Job.objects.filter(currentstep=models.Job.STATUS_AWAITING_DECISION).delete()
    models.Job.objects.filter(currentstep=models.Job.STATUS_EXECUTING_COMMANDS).update(
        currentstep=models.Job.STATUS_FAILED
    )
    models.Task.objects.filter(exitcode=None).update(
        exitcode=-1, stderror="MCP shut down while processing."
    )


def created_shared_directory_structure():
    dirs = (
        "arrange",
        "completed",
        "completed/transfers",
        "currentlyProcessing",
        "DIPbackups",
        "failed",
        "rejected",
        "sharedMicroServiceTasksConfigs",
        "sharedMicroServiceTasksConfigs/createXmlEventsAssist",
        "sharedMicroServiceTasksConfigs/generateAIP",
        "sharedMicroServiceTasksConfigs/generateAIP/bagit",
        "sharedMicroServiceTasksConfigs/processingMCPConfigs",
        "sharedMicroServiceTasksConfigs/transcoder",
        "sharedMicroServiceTasksConfigs/transcoder/defaultIcons",
        "SIPbackups",
        "tmp",
        "watchedDirectories",
        "watchedDirectories/activeTransfers",
        "watchedDirectories/activeTransfers/baggitDirectory",
        "watchedDirectories/activeTransfers/baggitZippedDirectory",
        "watchedDirectories/activeTransfers/dataverseTransfer",
        "watchedDirectories/activeTransfers/Dspace",
        "watchedDirectories/activeTransfers/maildir",
        "watchedDirectories/activeTransfers/standardTransfer",
        "watchedDirectories/activeTransfers/TRIM",
        "watchedDirectories/approveNormalization",
        "watchedDirectories/approveSubmissionDocumentationIngest",
        "watchedDirectories/quarantined",
        "watchedDirectories/SIPCreation",
        "watchedDirectories/SIPCreation/completedTransfers",
        "watchedDirectories/SIPCreation/SIPsUnderConstruction",
        "watchedDirectories/storeAIP",
        "watchedDirectories/system",
        "watchedDirectories/system/autoProcessSIP",
        "watchedDirectories/system/autoRestructureForCompliance",
        "watchedDirectories/system/createAIC",
        "watchedDirectories/system/reingestAIP",
        "watchedDirectories/uploadDIP",
        "watchedDirectories/uploadedDIPs",
        "watchedDirectories/workFlowDecisions",
        "watchedDirectories/workFlowDecisions/compressionAIPDecisions",
        "watchedDirectories/workFlowDecisions/createDip",
        "watchedDirectories/workFlowDecisions/createTree",
        "watchedDirectories/workFlowDecisions/examineContentsChoice",
        "watchedDirectories/workFlowDecisions/extractPackagesChoice",
        "watchedDirectories/workFlowDecisions/metadataReminder",
        "watchedDirectories/workFlowDecisions/quarantineTransfer",
        "watchedDirectories/workFlowDecisions/selectFormatIDToolIngest",
        "watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer",
        "www",
        "www/AIPsStore",
        "www/AIPsStore/transferBacklog",
        "www/AIPsStore/transferBacklog/arrange",
        "www/AIPsStore/transferBacklog/originals",
        "www/DIPsStore",
    )
    for d in dirs:
        d = os.path.join(django_settings.SHARED_DIRECTORY, d)
        if os.path.isdir(d):
            continue
        logger.info("Creating directory: %s", d)
        os.makedirs(d, mode=0o770)

    # Populate processing configurations
    for config in processing.BUILTIN_CONFIGS:
        processing.install_builtin_config(config)


def _except_hook_log_everything(exc_type, exc_value, exc_traceback):
    """
    Replacement for default exception handler that logs exceptions.
    """
    # Reference http://stackoverflow.com/a/16993115/2475775
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def signal_handler(signal, frame):
    """Used to handle the stop/kill command signals (SIGKILL)"""
    logger.info("Recieved signal %s in frame %s", signal, frame)

    shutdown_event.set()
    package_scheduler.shutdown()

    threads = threading.enumerate()
    for thread in threads:
        logger.warning("Not stopping %s %s", type(thread), thread)

    sys.stdout.flush()
    sys.stderr.flush()

    sys.exit(0)
    exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("This PID: %s", os.getpid())
    logger.info("User: %s", getpass.getuser())

    with open(DEFAULT_WORKFLOW) as workflow_file:
        try:
            workflow = load_workflow(workflow_file)
        except SchemaValidationError as err:
            logger.error("Workflow validation error: %s", err)
            sys.exit(1)

    metrics.start_prometheus_server()

    dicts.setup(
        shared_directory=django_settings.SHARED_DIRECTORY,
        processing_directory=django_settings.PROCESSING_DIRECTORY,
        watch_directory=django_settings.WATCH_DIRECTORY,
        rejected_directory=django_settings.REJECTED_DIRECTORY,
    )

    created_shared_directory_structure()

    debug_thread = threading.Thread(target=debugMonitor)
    debug_thread.start()

    output_flush_thread = threading.Thread(target=flushOutputs)
    output_flush_thread.start()

    rpc_thread = threading.Thread(
        target=RPCServer.start, args=(workflow, shutdown_event)
    )
    rpc_thread.start()

    cleanupOldDbEntriesOnNewRun()

    def new_dir_callback(path, watched_dir):
        createUnitAndJobChain(path, watched_dir, workflow)

    watch_dir_thread = threading.Thread(
        target=watch_directories,
        args=(workflow.get_wdirs(), shutdown_event, new_dir_callback),
    )
    watch_dir_thread.start()

    # Blocks until shutdown is called by a signal handler
    package_scheduler.start()
