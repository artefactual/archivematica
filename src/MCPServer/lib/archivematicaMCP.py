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

# From stdlib, alphabetical by import source
import ConfigParser
import errno
import getpass
import MySQLdb
import os
import pyinotify
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import traceback
import uuid

# From this project, alphabetical by import source
import watchDirectory
from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitFile import unitFile
from unitTransfer import unitTransfer
import RPCServer

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import databaseInterface
import databaseFunctions
from externals.singleInstance import singleinstance
from archivematicaFunctions import unicodeToStr
import storageService as storage_service

# Print SQL sent to the database interface 
databaseInterface.printSQL = True

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

def findOrCreateSipInDB(path, waitSleep=dbWaitSleep):
    """Matches a directory to a database sip by it's appended UUID, or path. If it doesn't find one, it will create one"""
    UUID = ""
    path = path.replace(config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

    #find UUID on end of SIP path
    uuidLen = -36
    if isUUID(path[uuidLen-1:-1]):
        UUID = path[uuidLen-1:-1]
        sql = """SELECT sipUUID FROM SIPs WHERE sipUUID = '%s';""" % UUID
        rows = databaseInterface.queryAllSQL(sql)
        if not rows:
            databaseFunctions.createSIP(path, UUID=UUID)
        


    if UUID == "":
        #Find it in the database
        sql = """SELECT sipUUID FROM SIPs WHERE currentPath = '%s';""" % MySQLdb.escape_string(path)
        #if waitSleep != 0:
            #time.sleep(waitSleep) #let db be updated by the microservice that moved it.
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        if not row:
            print "Not opening existing SIP:", UUID, "-", path
        while row != None:
            UUID = row[0]
            print "Opening existing SIP:", UUID, "-", path
            row = c.fetchone()
        sqlLock.release()


    #Create it
    if UUID == "":
        UUID = databaseFunctions.createSIP(path)
        print "DEBUG creating sip", path, UUID
    return UUID

def createUnitAndJobChain(path, config, terminate=False):
    path = unicodeToStr(path)
    if os.path.isdir(path):
            path = path + "/"
    print "createUnitAndJobChain", path, config
    unit = None
    if os.path.isdir(path):
        if config[3] == "SIP":
            UUID = findOrCreateSipInDB(path)
            unit = unitSIP(path, UUID)
        elif config[3] == "DIP":
            UUID = findOrCreateSipInDB(path)
            unit = unitDIP(path, UUID)
        elif config[3] == "Transfer":
            #UUID = findOrCreateSipInDB(path)
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
    #createUnitAndJobChain(path, config)
    #return
    try:
        if debug:
            print "DEBGUG alert watch path: ", path
        t = threading.Thread(target=createUnitAndJobChain, args=(path, config), kwargs={"terminate":terminate})
        t.daemon = True
        countOfCreateUnitAndJobChainThreaded += 1
        while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads ):
            if stopSignalReceived:
                print "Signal was received; stopping createUnitAndJobChainThreaded(path, config)"
                exit(0)
            print threading.activeCount().__str__()
            #print "DEBUG createUnitAndJobChainThreaded waiting on thread count", threading.activeCount()
            time.sleep(.5)
        countOfCreateUnitAndJobChainThreaded -= 1
        t.start()
    except Exception as inst:
        print "DEBUG EXCEPTION!"
        traceback.print_exc(file=sys.stdout)
        print type(inst)     # the exception instance
        print inst.args


def createDirectoryStructure():
    """ Create the shared directory structure for Archivematica. """
    # Poll trying to get storage service currently processing location
    while True:
        locations = storage_service.get_location(purpose='CP')
        if locations:
            break
        time.sleep(dbWaitSleep)

    if len(locations) > 1:
        print >>sys.stderr, 'WARNING: More than one currently processing location found, using the first one.', locations
    processing_path = locations[0]['path']
    print 'Processing path:', processing_path

    # Create shared directory structure

    # Only leaf nodes needed - parents will be created as needed
    dirs_to_make = [
        'arrange',
        'completed/transfers',
        'currentlyProcessing',
        'DIPbackups',
        'failed',
        'rejected',
        'SIPbackups',
        os.path.join('sharedMicroServiceTasksConfigs', 'transcoder', 'defaultIcons'),  # To copy into
        os.path.join('sharedMicroServiceTasksConfigs', 'processingMCPConfigs'),  # To copy into
        'staging',
        'tmp',
        os.path.join('www', 'AIPsStore', 'thumbnails'),
        os.path.join('www', 'AIPsStore', 'transferBacklog', 'originals'),
        os.path.join('www', 'AIPsStore', 'transferBacklog', 'arrange'),
        os.path.join('www', 'thumbnails'),
    ]

    # Get Watched Directories paths
    sql = """SELECT watchedDirectoryPath FROM WatchedDirectories;"""
    rows = databaseInterface.queryAllSQL(sql)
    for (db_path,) in rows:
        relative_path = db_path.replace('%watchDirectoryPath%', '')
        relative_path = os.path.join('watchedDirectories', relative_path)
        dirs_to_make.append(relative_path)

    # rwxrws--- = 2770
    mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_ISGID
    for d in dirs_to_make:
        d = os.path.join(processing_path, d)
        print 'Creating directory:', d
        try:
            os.makedirs(d, mode)
        except os.error as e:
            if e.errno == errno.EEXIST:
                print '  Skipping directory - already exists'
            else:
                raise

    # makedirs with mode doesn't seem to set permissions properly
    command = ['sudo', 'chown', '-R', 'archivematica:archivematica', processing_path]
    subprocess.call(command)
    command = ['sudo', 'chmod', '-R', '2770', processing_path]
    subprocess.call(command)

    # Copy files to the correct location
    copy_files = [
        (os.path.join(os.sep, 'usr', 'share', 'archivematica', 'processingMCPConfigs', 'defaultProcessingMCP.xml'),
            os.path.join(processing_path, 'sharedMicroServiceTasksConfigs', 'processingMCPConfigs', 'defaultProcessingMCP.xml')
        ),
        (os.path.join(os.sep, 'usr', 'share', 'archivematica', 'defaultIcons', 'default.jpg'),
            os.path.join(processing_path, 'sharedMicroServiceTasksConfigs', 'transcoder', 'defaultIcons', 'default.jpg')
        ),
    ]
    for (source, destination) in copy_files:
        print 'Copying', source, '->', destination
        if os.path.isfile(destination):
            print destination, 'already exists, skipping'
            continue
        try:
            shutil.copyfile(source, destination)
        except os.error as e:
            print "Could not copy to {}".format(destination)

    # Update config file so Archivematica knows where the shared directory is
    server_config_values = {
        # Archivematica expects directory paths to end with / (os.sep)
        'sharedDirectory': processing_path+os.sep,
        'watchDirectoryPath': '%(sharedDirectory)swatchedDirectories'+os.sep,
        'processingDirectory': '%(sharedDirectory)scurrentlyProcessing'+os.sep,
        'rejectedDirectory': '%(sharedDirectory)srejected'+os.sep,
    }
    archivematicaFunctions.set_server_config(server_config_values)
    client_config_values = {
        'sharedDirectoryMounted': processing_path+os.sep,
        'temp_dir': '%(sharedDirectory)stmp',
    }
    archivematicaFunctions.set_client_config(client_config_values)



def watchDirectories():
    """Start watching the watched directories defined in the WatchedDirectories table in the database."""
    rows = []
    sql = """SELECT watchedDirectoryPath, chain, onlyActOnDirectories, description FROM WatchedDirectories LEFT OUTER JOIN WatchedDirectoriesExpectedTypes ON WatchedDirectories.expectedType = WatchedDirectoriesExpectedTypes.pk"""
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        rows.append(row)
        row = c.fetchone()
    sqlLock.release()

    for row in rows:
        directory = row[0].replace("%watchDirectoryPath%", config.get('MCPServer', "watchDirectoryPath"), 1)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        for item in os.listdir(directory):
            if item == ".gitignore":
                continue
            item = item.decode("utf-8")
            path = os.path.join(unicode(directory), item)
            #createUnitAndJobChain(path, row)
            while(limitTaskThreads <= threading.activeCount() + reservedAsTaskProcessingThreads ):
                time.sleep(1)
            createUnitAndJobChainThreaded(path, row, terminate=False)
        actOnFiles=True
        if row[2]: #onlyActOnDirectories
            actOnFiles=False
        watchDirectory.archivematicaWatchDirectory(directory,variablesAdded=row, callBackFunctionAdded=createUnitAndJobChainThreaded, alertOnFiles=actOnFiles, interval=config.getint('MCPServer', "watchDirectoriesPollInterval"))

def signal_handler(signalReceived, frame):
    """Used to handle the stop/kill command signals (SIGKILL)"""
    print signalReceived, frame
    global stopSignalReceived
    stopSignalReceived = True
    threads = threading.enumerate()
    for thread in threads:
        if False and isinstance(thread, threading.Thread):
            try:
                print "not stopping: ", type(thread), thread
            except Exception as inst:
                print "DEBUG EXCEPTION!"
                print type(inst)     # the exception instance
                print inst.args
        elif isinstance(thread, pyinotify.ThreadedNotifier):
            print "stopping: ", type(thread), thread
            try:
                thread.stop()
            except Exception as inst:
                print >>sys.stderr, "DEBUG EXCEPTION!"
                print >>sys.stderr, type(inst)     # the exception instance
                print >>sys.stderr, inst.args
        else:
            print "not stopping: ", type(thread), thread
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(0)
    exit(0)

def debugMonitor():
    """Periodically prints out status of MCP, including whether the database lock is locked, thread count, etc."""
    global countOfCreateUnitAndJobChainThreaded
    while True:
        dblockstatus = "SQL Lock: Locked"
        if databaseInterface.sqlLock.acquire(False):
            databaseInterface.sqlLock.release()
            dblockstatus = "SQL Lock: Unlocked"
        print "<DEBUG type=\"archivematicaMCP\">", "\tDate Time: ", databaseInterface.getUTCDate(), "\tThreadCount: ", threading.activeCount(), "\tcountOfCreateUnitAndJobChainThreaded", countOfCreateUnitAndJobChainThreaded, dblockstatus, "</DEBUG>"
        time.sleep(3600)

def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)

def cleanupOldDbEntriesOnNewRun():
    sql = """DELETE FROM Jobs WHERE Jobs.currentStep = 'Awaiting decision';"""
    databaseInterface.runSQL(sql)
    
    sql = """UPDATE Jobs SET currentStep='Failed' WHERE currentStep='Executing command(s)';"""
    databaseInterface.runSQL(sql)
    
    sql = """UPDATE Tasks SET exitCode=-1, stdError='MCP shut down while processing.' WHERE exitCode IS NULL;"""
    databaseInterface.runSQL(sql)
    
    

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    si = singleinstance(config.get('MCPServer', "singleInstancePIDFile"))
    if si.alreadyrunning():
        print >>sys.stderr, "Another instance is already running. Killing PID:", si.pid
        si.kill()
    print "This PID: ", si.pid

    print "user: ", getpass.getuser()
    os.setuid(333)

    cleanupOldDbEntriesOnNewRun()
    createDirectoryStructure()

    t = threading.Thread(target=debugMonitor)
    t.daemon = True
    t.start()

    t = threading.Thread(target=flushOutputs)
    t.daemon = True
    t.start()

    watchDirectories()


    # debug 4545 https://projects.artefactual.com/issues/4545
    #print sys.stdout.encoding
    #print u'\u2019'
    
    # This is blocking the main thread with the worker loop
    RPCServer.startRPCServer()
