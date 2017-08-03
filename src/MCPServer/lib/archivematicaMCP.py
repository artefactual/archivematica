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
import logging
import logging.config
import getpass
import os
import signal
import sys
import threading
import time
import uuid

import django
django.setup()

from django.conf import settings as django_settings
from django.db.models import Q

# This project, alphabetical by import source
import watchDirectory
from utils import log_exceptions

from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitFile import unitFile
from unitTransfer import unitTransfer
from utils import isUUID
import RPCServer

from django_mysqlpool import auto_close_db
import databaseFunctions
from archivematicaFunctions import unicodeToStr
import dicts

from main.models import Job, SIP, Task, WatchedDirectory


countOfCreateUnitAndJobChainThreaded = 0

# time to sleep to allow db to be updated with the new location of a SIP
dbWaitSleep = 2

stopSignalReceived = False  # Tracks whether a sigkill has been received or not


DEFAULT_PROCESSING_CONFIG = u"""<processingMCP>
  <preconfiguredChoices>
    <!-- Store DIP: Store DIP -->
    <preconfiguredChoice>
      <appliesTo>5e58066d-e113-4383-b20b-f301ed4d751c</appliesTo>
      <goToChain>8d29eb3d-a8a8-4347-806e-3d8227ed44a1</goToChain>
    </preconfiguredChoice>
    <!-- Select compression level: 1 - fastest mode -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>ecfad581-b007-4612-a0e0-fcc551f4057f</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents: Skip examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Submission documentation & metadata): Identify using Siegfried -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>25a91595-37f0-4373-a89a-56a757353fb8</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 1 for "Normalize for preservation"): Normalize for preservation -->
    <preconfiguredChoice>
      <appliesTo>cb8e5706-e73f-472f-ad9b-d1236af8095f</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 2 for "Normalize for preservation"): Normalize for preservation -->
    <preconfiguredChoice>
      <appliesTo>7509e7dc-1e1b-4dce-8d21-e130515fce73</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Bind PIDs: No -->
    <preconfiguredChoice>
      <appliesTo>05357876-a095-4c11-86b5-a7fff01af668</appliesTo>
      <goToChain>fcfea449-158c-452c-a8ad-4ae009c4eaba</goToChain>
    </preconfiguredChoice>
    <!-- Create SIP(s): Create single SIP and continue processing -->
    <preconfiguredChoice>
      <appliesTo>bb194013-597c-4e4a-8493-b36d190f8717</appliesTo>
      <goToChain>61cfa825-120e-4b17-83e6-51a42b67d969</goToChain>
    </preconfiguredChoice>
    <!-- Delete packages after extraction: No -->
    <preconfiguredChoice>
      <appliesTo>f19926dd-8fb5-4c79-8ade-c83f61f55b40</appliesTo>
      <goToChain>72e8443e-a8eb-49a8-ba5f-76d52f960bde</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe files (OCR): Yes -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>5a9985d3-ce7e-4710-85c1-f74696770fa9</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Transfer): Identify using Siegfried -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>bed4eeb1-d654-4d97-b98d-40eb51d3d4bb</goToChain>
    </preconfiguredChoice>
    <!-- Store DIP location: Default location -->
    <preconfiguredChoice>
      <appliesTo>cd844b6e-ab3c-4bc6-b34f-7103f88715de</appliesTo>
      <goToChain>/api/v2/location/default/DS/</goToChain>
    </preconfiguredChoice>
    <!-- Generate transfer structure report: Yes -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>df54fec1-dae1-4ea6-8d17-a839ee7ac4a7</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on originals: No -->
    <preconfiguredChoice>
      <appliesTo>70fc7040-d4fb-4d19-a0e6-792387ca1006</appliesTo>
      <goToChain>3e891cc4-39d2-4989-a001-5107a009a223</goToChain>
    </preconfiguredChoice>
    <!-- Reminder: add metadata if desired: Continue -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm: Uncompressed -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>dc04c4c0-07ea-4796-b643-66d967ed33a4</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP: Yes -->
    <preconfiguredChoice>
      <appliesTo>2d32235c-02d4-4686-88a6-96f4d6c7b1c3</appliesTo>
      <goToChain>9efab23c-31dc-4cbd-a39d-bb1665460cbe</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on access derivatives: No -->
    <preconfiguredChoice>
      <appliesTo>8ce07e94-6130-4987-96f0-2399ad45c5c2</appliesTo>
      <goToChain>76befd52-14c3-44f9-838f-15a4e01624b0</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Ingest): Identify using Siegfried -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>664cbde3-e658-4288-87db-bd28266d83f5</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on preservation derivatives: No -->
    <preconfiguredChoice>
      <appliesTo>153c5f41-3cfb-47ba-9150-2dd44ebc27df</appliesTo>
      <goToChain>b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546</goToChain>
    </preconfiguredChoice>
    <!-- Assign UUIDs to directories: No -->
    <preconfiguredChoice>
      <appliesTo>bd899573-694e-4d33-8c9b-df0af802437d</appliesTo>
      <goToChain>891f60d0-1ba8-48d3-b39e-dd0934635d29</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP location: Default location -->
    <preconfiguredChoice>
      <appliesTo>b320ce81-9982-408a-9502-097d0daa48fa</appliesTo>
      <goToChain>/api/v2/location/default/AS/</goToChain>
    </preconfiguredChoice>
    <!-- Send transfer to quarantine: No -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Extract packages: No -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>79f1f5af-7694-48a4-b645-e42790bbf870</goToChain>
    </preconfiguredChoice>
    <!-- Approve normalization: Yes -->
    <preconfiguredChoice>
      <appliesTo>de909a42-c5b5-46e1-9985-c031b50e9d30</appliesTo>
      <goToChain>1e0df175-d56d-450d-8bee-7df1dc7ae815</goToChain>
    </preconfiguredChoice>
    <!-- Upload DIP: Do not upload DIP -->
    <preconfiguredChoice>
      <appliesTo>92879a29-45bf-4f0b-ac43-e64474f0f2f9</appliesTo>
      <goToChain>6eb8ebe7-fab3-4e4c-b9d7-14de17625baa</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""

AUTOMATED_PROCESSING_CONFIG = """<processingMCP>
  <preconfiguredChoices>
    <!-- Store DIP -->
    <preconfiguredChoice>
      <appliesTo>5e58066d-e113-4383-b20b-f301ed4d751c</appliesTo>
      <goToChain>8d29eb3d-a8a8-4347-806e-3d8227ed44a1</goToChain>
    </preconfiguredChoice>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>ecfad581-b007-4612-a0e0-fcc551f4057f</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Submission documentation & metadata) -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>25a91595-37f0-4373-a89a-56a757353fb8</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 1 for "Normalize for preservation") -->
    <preconfiguredChoice>
      <appliesTo>cb8e5706-e73f-472f-ad9b-d1236af8095f</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Normalize (match 2 for "Normalize for preservation") -->
    <preconfiguredChoice>
      <appliesTo>7509e7dc-1e1b-4dce-8d21-e130515fce73</appliesTo>
      <goToChain>612e3609-ce9a-4df6-a9a3-63d634d2d934</goToChain>
    </preconfiguredChoice>
    <!-- Create SIP(s) -->
    <preconfiguredChoice>
      <appliesTo>bb194013-597c-4e4a-8493-b36d190f8717</appliesTo>
      <goToChain>61cfa825-120e-4b17-83e6-51a42b67d969</goToChain>
    </preconfiguredChoice>
    <!-- Delete packages after extraction -->
    <preconfiguredChoice>
      <appliesTo>f19926dd-8fb5-4c79-8ade-c83f61f55b40</appliesTo>
      <goToChain>72e8443e-a8eb-49a8-ba5f-76d52f960bde</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe files (OCR) -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>5a9985d3-ce7e-4710-85c1-f74696770fa9</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Transfer) -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>bed4eeb1-d654-4d97-b98d-40eb51d3d4bb</goToChain>
    </preconfiguredChoice>
    <!-- Store DIP location -->
    <preconfiguredChoice>
      <appliesTo>cd844b6e-ab3c-4bc6-b34f-7103f88715de</appliesTo>
      <goToChain>/api/v2/location/default/DS/</goToChain>
    </preconfiguredChoice>
    <!-- Generate transfer structure report -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>df54fec1-dae1-4ea6-8d17-a839ee7ac4a7</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on originals -->
    <preconfiguredChoice>
      <appliesTo>70fc7040-d4fb-4d19-a0e6-792387ca1006</appliesTo>
      <goToChain>3e891cc4-39d2-4989-a001-5107a009a223</goToChain>
    </preconfiguredChoice>
    <!-- Reminder: add metadata if desired -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>dc04c4c0-07ea-4796-b643-66d967ed33a4</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP -->
    <preconfiguredChoice>
      <appliesTo>2d32235c-02d4-4686-88a6-96f4d6c7b1c3</appliesTo>
      <goToChain>9efab23c-31dc-4cbd-a39d-bb1665460cbe</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on access derivatives -->
    <preconfiguredChoice>
      <appliesTo>8ce07e94-6130-4987-96f0-2399ad45c5c2</appliesTo>
      <goToChain>76befd52-14c3-44f9-838f-15a4e01624b0</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Ingest) -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>664cbde3-e658-4288-87db-bd28266d83f5</goToChain>
    </preconfiguredChoice>
    <!-- Perform policy checks on preservation derivatives -->
    <preconfiguredChoice>
      <appliesTo>153c5f41-3cfb-47ba-9150-2dd44ebc27df</appliesTo>
      <goToChain>b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP location -->
    <preconfiguredChoice>
      <appliesTo>b320ce81-9982-408a-9502-097d0daa48fa</appliesTo>
      <goToChain>/api/v2/location/default/AS/</goToChain>
    </preconfiguredChoice>
    <!-- Send transfer to quarantine -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Extract packages -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>79f1f5af-7694-48a4-b645-e42790bbf870</goToChain>
    </preconfiguredChoice>
    <!-- Approve normalization -->
    <preconfiguredChoice>
      <appliesTo>de909a42-c5b5-46e1-9985-c031b50e9d30</appliesTo>
      <goToChain>1e0df175-d56d-450d-8bee-7df1dc7ae815</goToChain>
    </preconfiguredChoice>
    <!-- Upload DIP -->
    <preconfiguredChoice>
      <appliesTo>92879a29-45bf-4f0b-ac43-e64474f0f2f9</appliesTo>
      <goToChain>0fe9842f-9519-4067-a691-8a363132ae24</goToChain>
    </preconfiguredChoice>
    <!-- Bind PIDs?: No -->
    <preconfiguredChoice>
      <appliesTo>05357876-a095-4c11-86b5-a7fff01af668</appliesTo>
      <goToChain>fcfea449-158c-452c-a8ad-4ae009c4eaba</goToChain>
    </preconfiguredChoice>
    <!-- Assign UUIDs to directories?: No -->
    <preconfiguredChoice>
      <appliesTo>bd899573-694e-4d33-8c9b-df0af802437d</appliesTo>
      <goToChain>891f60d0-1ba8-48d3-b39e-dd0934635d29</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""


def fetchUUIDFromPath(path):
    # find UUID on end of SIP path
    uuidLen = -36
    if isUUID(path[uuidLen - 1:-1]):
        return path[uuidLen - 1:-1]


def findOrCreateSipInDB(path, waitSleep=dbWaitSleep, unit_type='SIP'):
    """Matches a directory to a database sip by it's appended UUID, or path. If it doesn't find one, it will create one"""
    path = path.replace(django_settings.SHARED_DIRECTORY, "%sharedPath%", 1)

    query = Q(currentpath=path)

    # Find UUID on end of SIP path
    UUID = fetchUUIDFromPath(path)
    sip = None
    if UUID:
        query = query | Q(uuid=UUID)

    sips = SIP.objects.filter(query)
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
            logger.error('More than one SIP for path %s and/or UUID %s, using first result', path, UUID)
    if count > 0:
        sip = sips[0]
        UUID = sip.uuid
        logger.info('Using existing SIP %s at %s', UUID, path)
    else:
        logger.info('Not using existing SIP %s at %s', UUID, path)

    if sip is None:
        # Create it
        # Note that if UUID is None here, a new UUID will be generated
        # and returned by the function; otherwise it returns the
        # value that was passed in.
        UUID = databaseFunctions.createSIP(path, UUID=UUID)
        logger.info('Creating SIP %s at %s', UUID, path)
    else:
        current_path = sip.currentpath
        if current_path != path and unit_type == 'SIP':
            # Ensure path provided matches path in DB
            sip.currentpath = path
            sip.save()

    return UUID


@log_exceptions
@auto_close_db
def createUnitAndJobChain(path, config, terminate=False):
    path = unicodeToStr(path)
    if os.path.isdir(path):
        path = path + "/"
    logger.debug('Creating unit and job chain for %s with %s', path, config)
    unit = None
    if os.path.isdir(path):
        if config[3] == "SIP":
            UUID = findOrCreateSipInDB(path)
            unit = unitSIP(path, UUID)
        elif config[3] == "DIP":
            UUID = findOrCreateSipInDB(path, unit_type='DIP')
            unit = unitDIP(path, UUID)
        elif config[3] == "Transfer":
            unit = unitTransfer(path)
    elif os.path.isfile(path):
        if config[3] == "Transfer":
            unit = unitTransfer(path)
        else:
            return
            UUID = uuid.uuid4()
            unit = unitFile(path, UUID)
    else:
        return
    jobChain(unit, config[1])

    if terminate:
        exit(0)


def createUnitAndJobChainThreaded(path, config, terminate=True):
    global countOfCreateUnitAndJobChainThreaded
    try:
        logger.debug('Watching path %s', path)
        t = threading.Thread(target=createUnitAndJobChain, args=(path, config), kwargs={"terminate": terminate})
        t.daemon = True
        countOfCreateUnitAndJobChainThreaded += 1
        while(django_settings.LIMIT_TASK_THREADS <= threading.activeCount() + django_settings.RESERVED_AS_TASK_PROCESSING_THREADS):
            if stopSignalReceived:
                logger.info('Signal was received; stopping createUnitAndJobChainThreaded(path, config)')
                exit(0)
            logger.debug('Active thread count: %s', threading.activeCount())
            time.sleep(.5)
        countOfCreateUnitAndJobChainThreaded -= 1
        t.start()
    except Exception:
        logger.exception('Error creating threads to watch directories')


def watchDirectories():
    """Start watching the watched directories defined in the WatchedDirectories table in the database."""
    watched_dir_path = django_settings.WATCH_DIRECTORY
    interval = django_settings.WATCH_DIRECTORY_INTERVAL

    watched_directories = WatchedDirectory.objects.all()

    for watched_directory in watched_directories:
        directory = watched_directory.watched_directory_path.replace("%watchDirectoryPath%", watched_dir_path, 1)

        # Tuple of variables that may be used by a callback
        row = (watched_directory.watched_directory_path, watched_directory.chain_id, watched_directory.only_act_on_directories, watched_directory.expected_type.description)

        if not os.path.isdir(directory):
            os.makedirs(directory)
        for item in os.listdir(directory):
            if item == ".gitignore":
                continue
            item = item.decode("utf-8")
            path = os.path.join(unicode(directory), item)
            while(django_settings.LIMIT_TASK_THREADS <= threading.activeCount() + django_settings.RESERVED_AS_TASK_PROCESSING_THREADS):
                time.sleep(1)
            createUnitAndJobChainThreaded(path, row, terminate=False)
        actOnFiles = True
        if watched_directory.only_act_on_directories:
            actOnFiles = False
        watchDirectory.archivematicaWatchDirectory(
            directory,
            variablesAdded=row,
            callBackFunctionAdded=createUnitAndJobChainThreaded,
            alertOnFiles=actOnFiles,
            interval=interval,
        )


def signal_handler(signalReceived, frame):
    """Used to handle the stop/kill command signals (SIGKILL)"""
    logger.info('Recieved signal %s in frame %s', signalReceived, frame)
    global stopSignalReceived
    stopSignalReceived = True
    threads = threading.enumerate()
    for thread in threads:
        logger.warning('Not stopping %s %s', type(thread), thread)
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)
    exit(0)


@log_exceptions
@auto_close_db
def debugMonitor():
    """Periodically prints out status of MCP, including whether the database lock is locked, thread count, etc."""
    global countOfCreateUnitAndJobChainThreaded
    while True:
        logger.debug('Debug monitor: datetime: %s', databaseFunctions.getUTCDate())
        logger.debug('Debug monitor: thread count: %s', threading.activeCount())
        logger.debug('Debug monitor: created job chain threaded: %s', countOfCreateUnitAndJobChainThreaded)
        time.sleep(3600)


@log_exceptions
@auto_close_db
def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)


def cleanupOldDbEntriesOnNewRun():
    Job.objects.filter(currentstep=Job.STATUS_AWAITING_DECISION).delete()
    Job.objects.filter(currentstep=Job.STATUS_EXECUTING_COMMANDS).update(currentstep=Job.STATUS_FAILED)
    Task.objects.filter(exitcode=None).update(exitcode=-1, stderror="MCP shut down while processing.")


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
        "www/DIPsStore"
    )
    for d in dirs:
        d = os.path.join(django_settings.SHARED_DIRECTORY, d)
        if os.path.isdir(d):
            continue
        logger.info('Creating directory: %s', d)
        os.makedirs(d, mode=0o770)

    # Populate processing configurations
    proc_configs = (
        ('defaultProcessingMCP.xml', DEFAULT_PROCESSING_CONFIG),
        ('automatedProcessingMCP.xml', AUTOMATED_PROCESSING_CONFIG),
    )
    for item in proc_configs:
        path = os.path.join(django_settings.SHARED_DIRECTORY, 'sharedMicroServiceTasksConfigs/processingMCPConfigs', item[0])
        if os.path.isfile(path):
            continue
        with open(path, 'w') as fd:
            fd.write(item[1].encode('utf-8'))


def _except_hook_log_everything(exc_type, exc_value, exc_traceback):
    """
    Replacement for default exception handler that logs exceptions.
    """
    # Reference http://stackoverflow.com/a/16993115/2475775
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == '__main__':
    logger = logging.getLogger("archivematica.mcp.server")

    # Replace exception handler with one that logs exceptions
    sys.excepthook = _except_hook_log_everything

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info('This PID: %s', os.getpid())
    logger.info('User: %s', getpass.getuser())

    dicts.setup(
        shared_directory=django_settings.SHARED_DIRECTORY,
        processing_directory=django_settings.PROCESSING_DIRECTORY,
        watch_directory=django_settings.WATCH_DIRECTORY,
        rejected_directory=django_settings.REJECTED_DIRECTORY,
    )

    created_shared_directory_structure()

    t = threading.Thread(target=debugMonitor)
    t.daemon = True
    t.start()

    t = threading.Thread(target=flushOutputs)
    t.daemon = True
    t.start()
    cleanupOldDbEntriesOnNewRun()
    watchDirectories()

    # This is blocking the main thread with the worker loop
    RPCServer.startRPCServer()
