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
import os
from pwd import getpwnam
import pyinotify
import signal
import sys
import threading
import time
import uuid

import django
sys.path.append('/usr/share/archivematica/dashboard')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'
django.setup()

# This project, alphabetical by import source
import watchDirectory
from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitFile import unitFile
from unitTransfer import unitTransfer
import RPCServer
from utils import log_exceptions

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import databaseFunctions
from externals.singleInstance import singleinstance
from archivematicaFunctions import unicodeToStr

from main.models import Job, SIP, Task, WatchedDirectory

global countOfCreateUnitAndJobChainThreaded
countOfCreateUnitAndJobChainThreaded = 0

config = ConfigParser.SafeConfigParser()
config.read("/etc/archivematica/MCPServer/serverConfig.conf")

#time to sleep to allow db to be updated with the new location of a SIP
dbWaitSleep = 2


limitTaskThreads = config.getint('Protocol', "limitTaskThreads")
limitTaskThreadsSleep = config.getfloat('Protocol', "limitTaskThreadsSleep")
limitGearmanConnectionsSemaphore = threading.Semaphore(value=config.getint('Protocol', "limitGearmanConnections"))
reservedAsTaskProcessingThreads = config.getint('Protocol', "reservedAsTaskProcessingThreads")
debug = False #Used to print additional debugging information
stopSignalReceived = False #Tracks whether a sigkill has been received or not

def isUUID(uuid):
    """Return boolean of whether it's string representation of a UUID v4"""
    split = uuid.split("-")
    if len(split) != 5 \
    or len(split[0]) != 8 \
    or len(split[1]) != 4 \
    or len(split[2]) != 4 \
    or len(split[3]) != 4 \
    or len(split[4]) != 12 :
        return False
    return True

def fetchUUIDFromPath(path):
    #find UUID on end of SIP path
    uuidLen = -36
    if isUUID(path[uuidLen-1:-1]):
        return path[uuidLen-1:-1]

def findOrCreateSipInDB(path, waitSleep=dbWaitSleep, unit_type='SIP'):
    """Matches a directory to a database sip by it's appended UUID, or path. If it doesn't find one, it will create one"""
    path = path.replace(config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

    # Find UUID on end of SIP path
    UUID = fetchUUIDFromPath(path)
    if UUID:
        try:
            sip = SIP.objects.get(uuid=UUID)
        except SIP.DoesNotExist:
            databaseFunctions.createSIP(path, UUID=UUID)
        else:
            current_path = sip.currentpath
            if current_path != path and unit_type == 'SIP':
                # Ensure path provided matches path in DB
                sip.currentpath = path
                sip.save()
    else:
        #Find it in the database
        sips = SIP.objects.filter(currentpath=path)
        count = sips.count()
        if count > 1:
            logger.warning('More than one SIP for path %s, using first result', path)
        if count > 0:
            UUID = sips[0].uuid
            logger.info('Using existing SIP %s at %s', UUID, path)
        else:
            logger.info('Not using existing SIP %s at %s', UUID, path)

    #Create it
    if not UUID:
        UUID = databaseFunctions.createSIP(path)
        logger.info('Creating SIP %s at %s', UUID, path)
    return UUID

@log_exceptions
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
        t = threading.Thread(target=createUnitAndJobChain, args=(path, config), kwargs={"terminate":terminate})
        t.daemon = True
        countOfCreateUnitAndJobChainThreaded += 1
        while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads ):
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
            while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads ):
                time.sleep(1)
            createUnitAndJobChainThreaded(path, row, terminate=False)
        actOnFiles=True
        if watched_directory.only_act_on_directories:
            actOnFiles=False
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
        if isinstance(thread, pyinotify.ThreadedNotifier):
            logger.info('Stopping %s %s', type(thread), thread)
            try:
                thread.stop()
            except Exception as inst:
                logger.exception('Error stopping thread')
        else:
            logger.warning('Not stopping %s %s', type(thread), thread)
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)
    exit(0)

@log_exceptions
def debugMonitor():
    """Periodically prints out status of MCP, including whether the database lock is locked, thread count, etc."""
    global countOfCreateUnitAndJobChainThreaded
    while True:
        dblockstatus = "SQL Lock: Locked"
        if databaseInterface.sqlLock.acquire(False):
            databaseInterface.sqlLock.release()
            dblockstatus = "SQL Lock: Unlocked"
        logger.debug('Debug monitor: datetime: %s', databaseFunctions.getUTCDate())
        logger.debug('Debug monitor: thread count: %s', threading.activeCount())
        logger.debug('Debug monitor: created job chain threaded: %s', countOfCreateUnitAndJobChainThreaded)
        logger.debug('Debug monitor: DB lock status: %s', dblockstatus)
        time.sleep(3600)

@log_exceptions
def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)

def cleanupOldDbEntriesOnNewRun():
    Job.objects.filter(currentstep='Awaiting decision').delete()
    Job.objects.filter(currentstep='Executing command(s)').update(currentstep='Failed')
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
        'debug_logfile': {
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
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'archivematica.mcp.server': {
            'handlers': ['debug_logfile', 'logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'archivematica.common': {
            'handlers': ['debug_logfile', 'logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['null'],
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['logfile'],
        'level': 'INFO',
    }
}

if __name__ == '__main__':
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("archivematica.mcp.server")

    # Replace exception handler with one that logs exceptions
    sys.excepthook = _except_hook_log_everything

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    si = singleinstance(config.get('MCPServer', "singleInstancePIDFile"))
    if si.alreadyrunning():
        logger.warning('Another instance is already running. Killing PID %s', si.pid)
        si.kill()

    logger.info('This PID: %s', si.pid)

    import getpass
    logger.info('User: %s', getpass.getuser())
    os.setuid(getpwnam('archivematica').pw_uid)

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
