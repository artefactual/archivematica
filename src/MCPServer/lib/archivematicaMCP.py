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
import ConfigParser
import logging
import logging.config
import getpass
import os
import signal
import sys
import threading
import time
import uuid

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

import django
django.setup()

from django.db.models import Q

# This project, alphabetical by import source
import watchDirectory
import RPCServer
from utils import log_exceptions

from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitFile import unitFile
from unitTransfer import unitTransfer

from django_mysqlpool import auto_close_db
import databaseFunctions
from archivematicaFunctions import unicodeToStr

from main.models import Job, SIP, Task, WatchedDirectory

global countOfCreateUnitAndJobChainThreaded
countOfCreateUnitAndJobChainThreaded = 0

config = ConfigParser.SafeConfigParser()
config.read("/etc/archivematica/MCPServer/serverConfig.conf")

# time to sleep to allow db to be updated with the new location of a SIP
dbWaitSleep = 2


limitTaskThreads = config.getint('Protocol', "limitTaskThreads")
limitTaskThreadsSleep = config.getfloat('Protocol', "limitTaskThreadsSleep")
limitGearmanConnectionsSemaphore = threading.Semaphore(value=config.getint('Protocol', "limitGearmanConnections"))
reservedAsTaskProcessingThreads = config.getint('Protocol', "reservedAsTaskProcessingThreads")
stopSignalReceived = False  # Tracks whether a sigkill has been received or not


DEFAULT_PROCESSING_CONFIG = u"""<processingMCP>
  <preconfiguredChoices>
    <!-- Send to quarantine? -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Display metadata reminder -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Remove from quarantine -->
    <preconfiguredChoice>
      <appliesTo>19adb668-b19a-4fcb-8938-f49d7485eaf3</appliesTo>
      <goToChain>333643b7-122a-4019-8bef-996443f3ecc5</goToChain>
      <delay unitCtime="yes">2419200.0</delay>
    </preconfiguredChoice>
    <!-- Extract packages -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>01d80b27-4ad1-4bd1-8f8d-f819f18bf685</goToChain>
    </preconfiguredChoice>
    <!-- Delete extracted packages -->
    <preconfiguredChoice>
      <appliesTo>f19926dd-8fb5-4c79-8ade-c83f61f55b40</appliesTo>
      <goToChain>85b1e45d-8f98-4cae-8336-72f40e12cbef</goToChain>
    </preconfiguredChoice>
    <!-- Select pre-normalize file format identification command -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
    </preconfiguredChoice>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>414da421-b83f-4648-895f-a34840e3c3f5</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe file -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53</goToChain>
    </preconfiguredChoice>
    <!-- Transfer tree diagram -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>e9eaef1e-c2e0-4e3b-b942-bfb537162795</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""

AUTOMATED_PROCESSING_CONFIG = """<processingMCP>
  <preconfiguredChoices>
    <!-- Select file format identification command (Submission documentation & metadata) -->
    <preconfiguredChoice>
      <appliesTo>087d27be-c719-47d8-9bbb-9a7d8b609c44</appliesTo>
      <goToChain>25a91595-37f0-4373-a89a-56a757353fb8</goToChain>
    </preconfiguredChoice>
    <!-- Generate transfer structure report -->
    <preconfiguredChoice>
      <appliesTo>56eebd45-5600-4768-a8c2-ec0114555a3d</appliesTo>
      <goToChain>df54fec1-dae1-4ea6-8d17-a839ee7ac4a7</goToChain>
    </preconfiguredChoice>
    <!-- Select compression level -->
    <preconfiguredChoice>
      <appliesTo>01c651cb-c174-4ba4-b985-1d87a44d6754</appliesTo>
      <goToChain>414da421-b83f-4648-895f-a34840e3c3f5</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Ingest) -->
    <preconfiguredChoice>
      <appliesTo>7a024896-c4f7-4808-a240-44c87c762bc5</appliesTo>
      <goToChain>664cbde3-e658-4288-87db-bd28266d83f5</goToChain>
    </preconfiguredChoice>
    <!-- Reminder: add metadata if desired -->
    <preconfiguredChoice>
      <appliesTo>eeb23509-57e2-4529-8857-9d62525db048</appliesTo>
      <goToChain>5727faac-88af-40e8-8c10-268644b0142d</goToChain>
    </preconfiguredChoice>
    <!-- Create SIP(s) -->
    <preconfiguredChoice>
      <appliesTo>bb194013-597c-4e4a-8493-b36d190f8717</appliesTo>
      <goToChain>61cfa825-120e-4b17-83e6-51a42b67d969</goToChain>
    </preconfiguredChoice>
    <!-- Transcribe files (OCR) -->
    <preconfiguredChoice>
      <appliesTo>7079be6d-3a25-41e6-a481-cee5f352fe6e</appliesTo>
      <goToChain>5a9985d3-ce7e-4710-85c1-f74696770fa9</goToChain>
    </preconfiguredChoice>
    <!-- Delete packages after extraction -->
    <preconfiguredChoice>
      <appliesTo>f19926dd-8fb5-4c79-8ade-c83f61f55b40</appliesTo>
      <goToChain>72e8443e-a8eb-49a8-ba5f-76d52f960bde</goToChain>
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
    <!-- Send transfer to quarantine -->
    <preconfiguredChoice>
      <appliesTo>755b4177-c587-41a7-8c52-015277568302</appliesTo>
      <goToChain>d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e</goToChain>
    </preconfiguredChoice>
    <!-- Select compression algorithm -->
    <preconfiguredChoice>
      <appliesTo>01d64f58-8295-4b7b-9cab-8f1b153a504f</appliesTo>
      <goToChain>9475447c-9889-430c-9477-6287a9574c5b</goToChain>
    </preconfiguredChoice>
    <!-- Examine contents -->
    <preconfiguredChoice>
      <appliesTo>accea2bf-ba74-4a3a-bb97-614775c74459</appliesTo>
      <goToChain>e0a39199-c62a-4a2f-98de-e9d1116460a8</goToChain>
    </preconfiguredChoice>
    <!-- Select file format identification command (Transfer) -->
    <preconfiguredChoice>
      <appliesTo>f09847c2-ee51-429a-9478-a860477f6b8d</appliesTo>
      <goToChain>bed4eeb1-d654-4d97-b98d-40eb51d3d4bb</goToChain>
    </preconfiguredChoice>
    <!-- Extract packages -->
    <preconfiguredChoice>
      <appliesTo>dec97e3c-5598-4b99-b26e-f87a435a6b7f</appliesTo>
      <goToChain>79f1f5af-7694-48a4-b645-e42790bbf870</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP -->
    <preconfiguredChoice>
      <appliesTo>2d32235c-02d4-4686-88a6-96f4d6c7b1c3</appliesTo>
      <goToChain>9efab23c-31dc-4cbd-a39d-bb1665460cbe</goToChain>
    </preconfiguredChoice>
    <!-- Approve normalization -->
    <preconfiguredChoice>
      <appliesTo>de909a42-c5b5-46e1-9985-c031b50e9d30</appliesTo>
      <goToChain>1e0df175-d56d-450d-8bee-7df1dc7ae815</goToChain>
    </preconfiguredChoice>
    <!-- Store AIP location -->
    <preconfiguredChoice>
      <appliesTo>b320ce81-9982-408a-9502-097d0daa48fa</appliesTo>
      <goToChain>/api/v2/location/default/AS/</goToChain>
    </preconfiguredChoice>
  </preconfiguredChoices>
</processingMCP>
"""


def isUUID(uuid):
    """Return boolean of whether it's string representation of a UUID v4"""
    split = uuid.split("-")
    if len(split) != 5 \
            or len(split[0]) != 8 \
            or len(split[1]) != 4 \
            or len(split[2]) != 4 \
            or len(split[3]) != 4 \
            or len(split[4]) != 12:
        return False
    return True


def fetchUUIDFromPath(path):
    # find UUID on end of SIP path
    uuidLen = -36
    if isUUID(path[uuidLen - 1:-1]):
        return path[uuidLen - 1:-1]


def findOrCreateSipInDB(path, waitSleep=dbWaitSleep, unit_type='SIP'):
    """Matches a directory to a database sip by it's appended UUID, or path. If it doesn't find one, it will create one"""
    path = path.replace(config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

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
        while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads):
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
    watched_dir_path = config.get('MCPServer', "watchDirectoryPath")
    interval = config.getint('MCPServer', "watchDirectoriesPollInterval")

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
            while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads):
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


def _except_hook_log_everything(exc_type, exc_value, exc_traceback):
    """
    Replacement for default exception handler that logs exceptions.
    """
    # Reference http://stackoverflow.com/a/16993115/2475775
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(levelname)-8s  %(asctime)s  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'verboselogfile': {
            'level': 'DEBUG',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPServer/MCPServer.debug.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 4 MiB
        },
        'logfile': {
            'level': 'INFO',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPServer/MCPServer.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 4 MiB
        },
    },
    'loggers': {
        'archivematica': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['logfile', 'verboselogfile'],
        'level': 'WARNING',
    },
}

if __name__ == '__main__':
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("archivematica.mcp.server")

    # Replace exception handler with one that logs exceptions
    sys.excepthook = _except_hook_log_everything

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info('This PID: %s', os.getpid())
    logger.info('User: %s', getpass.getuser())

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
