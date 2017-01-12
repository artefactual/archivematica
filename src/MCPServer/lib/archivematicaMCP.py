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

#~DOC~
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

# TODO: deal with this outside the application
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
for item in ('/usr/lib/archivematica/archivematicaCommon', '/usr/share/archivematica/dashboard', '/usr/lib/archivematica/MCPServer'):
    if item not in sys.path:
        sys.path.append(item)

import django
django.setup()

from django.db.models import Q
from django.utils import timezone

# This project, alphabetical by import source
import watchDirectory
import gRPCServer
from utils import log_exceptions, get_uuid_from_path

from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitTransfer import unitTransfer

from django_mysqlpool import auto_close_db
from databaseFunctions import createSIP
from archivematicaFunctions import unicodeToStr
import workflow
import protos.workflow_pb2 as workflow_pb2

from main.models import Job, SIP, Task


config = ConfigParser.SafeConfigParser()
config.read("/etc/archivematica/MCPServer/serverConfig.conf")

limitTaskThreads = config.getint('Protocol', "limitTaskThreads")
limitTaskThreadsSleep = config.getfloat('Protocol', "limitTaskThreadsSleep")
limitGearmanConnectionsSemaphore = threading.Semaphore(value=config.getint('Protocol', "limitGearmanConnections"))
reservedAsTaskProcessingThreads = config.getint('Protocol', "reservedAsTaskProcessingThreads")
stopSignalReceived = False  # Tracks whether a sigkill has been received or not


def findOrCreateSipInDB(path, unit_type):
    """
    Matches a directory to a database sip by it's appended UUID, or path. If it
    doesn't find one, it will create one.
    """
    path = path.replace(config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

    query = Q(currentpath=path)

    # Find UUID on end of SIP path
    UUID = get_uuid_from_path(path)
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
        UUID = createSIP(path, UUID=UUID)
        logger.info('Creating SIP %s at %s', UUID, path)
    else:
        current_path = sip.currentpath
        if current_path != path and unit_type == workflow_pb2.WatchedDirectory.SIP:
            # Ensure path provided matches path in DB
            sip.currentpath = path
            sip.save()

    return UUID


@log_exceptions
@auto_close_db
def createUnitAndJobChain(path, config, terminate=False):
    path = unicodeToStr(path)
    if os.path.isdir(path):
        path = os.path.join(path, '')
    unit = None
    unit_type = config[3]
    unit_type_name = workflow_pb2.WatchedDirectory.WatchedDirectoryType.Name(unit_type)

    if os.path.isdir(path):
        if unit_type == workflow_pb2.WatchedDirectory.SIP:
            UUID = findOrCreateSipInDB(path, unit_type)
            unit = unitSIP(path, UUID)
        elif unit_type == workflow_pb2.WatchedDirectory.DIP:
            UUID = findOrCreateSipInDB(path, unit_type)
            unit = unitDIP(path, UUID)
        elif unit_type == workflow_pb2.WatchedDirectory.TRANSFER:
            unit = unitTransfer(path)
    elif os.path.isfile(path):
        if unit_type == workflow_pb2.WatchedDirectory.TRANSFER:
            unit = unitTransfer(path)

    if unit is None:
        logger.warning('Unit not created! path="%s" type="%s"', path, unit_type_name)
        return
    logger.debug('New unit created! uuid="%s" type="%s"', unit.UUID, unit_type_name)

    # Start chain, passing: unit, chainId, workflow and unit_choices
    jobChain(unit, config[1], config[4], config[5])

    if terminate:
        exit(0)


def createUnitAndJobChainThreaded(path, config, terminate=True):
    try:
        logger.debug('Watching path %s', path)
        t = threading.Thread(target=createUnitAndJobChain, args=(path, config), kwargs={"terminate": terminate})
        t.daemon = True
        while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads ):
            if stopSignalReceived:
                logger.info('Signal was received; stopping createUnitAndJobChainThreaded(path, config)')
                exit(0)
            logger.debug('Active thread count: %s', threading.activeCount())
            time.sleep(.5)
        t.start()
    except Exception:
        logger.exception('Error creating threads to watch directories')


def watchDirectories(workflow, unit_choices):
    """
    Start watching the directories listed in the workflow data.
    """
    watched_dir_path = config.get('MCPServer', "watchDirectoryPath")
    interval = config.getint('MCPServer', "watchDirectoriesPollInterval")

    for watched_directory in workflow.watchedDirectories:
        directory = os.path.join(watched_dir_path, watched_directory.path.lstrip('/'), '')

        # Tuple of variables that may be used by a callback.
        # This could be a collections.namedtuple.
        row = (
            watched_directory.path,
            watched_directory.chainId,
            watched_directory.onlyDirs,
            watched_directory.type,
            workflow,
            unit_choices
        )

        if not os.path.isdir(directory):
            os.makedirs(directory)

        # Start processing of existing directories.
        for item in os.listdir(directory):
            if item == ".gitignore":
                continue
            item = item.decode("utf-8")
            path = os.path.join(directory, item)
            while limitTaskThreads <= (threading.activeCount() + reservedAsTaskProcessingThreads):
                time.sleep(1)
            createUnitAndJobChainThreaded(path, row, terminate=False)

        watchDirectory.archivematicaWatchDirectory(
            directory,
            variablesAdded=row,
            callBackFunctionAdded=createUnitAndJobChainThreaded,
            alertOnFiles=watched_directory.onlyDirs,
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
def print_internal_state(signal_received, frame):
    logger.debug('Debug monitor: datetime: %s', timezone.now())
    logger.debug('Debug monitor: thread count: %s', threading.activeCount())


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
            'format': '%(levelname)-8s  %(asctime)s  %(thread)d  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'archivematica': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['logfile', 'verboselogfile', 'console'],
        'level': 'WARNING',
    },
}


class UnitChoices(dict):
    """
    Thread-safe store of MCP's weirdest global shared state data structure.
    Currently, this is a subclass of dict that is expected to be used via the
    with statement. Implementation details may change but the interface will
    be maintained, e.g. see http://stackoverflow.com/a/3387975.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._lock = threading.Lock()

    def __repr__(self):
        return 'UnitChoices:' + dict.__repr__(self)

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self._lock.release()


if __name__ == '__main__':
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("archivematica.mcp.server")

    logger.info('Hello! pid=%s user=%s', os.getpid(), getpass.getuser())

    # Replace exception handler with one that logs exceptions
    sys.excepthook = _except_hook_log_everything

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, print_internal_state)

    unit_choices = UnitChoices()

    try:
        workflow_client = workflow.get_client()
        workflow = workflow_client.get_workflow('default')
    except workflow.Error:
        logger.error('Workflow client error: %s', exc_info=True)
        sys.exit(1)

    cleanupOldDbEntriesOnNewRun()

    watchDirectories(workflow, unit_choices)

    # This is going to block the main thread
    gRPCServer.start(workflow, unit_choices)
