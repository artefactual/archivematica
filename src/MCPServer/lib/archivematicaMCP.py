#!/usr/bin/python -OO

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

# @package Archivematica
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

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
import threading
import watchDirectory
from jobChain import jobChain
from unitSIP import unitSIP
from unitDIP import unitDIP
from unitFile import unitFile
from unitTransfer import unitTransfer
from pyinotify import ThreadedNotifier
import transferD
import RPCServer
import MySQLdb

import signal
import os
import pyinotify
# from archivematicaReplacementDics import replacementDics
# from MCPlogging import *
# from MCPloggingSQL import getUTCDate
import ConfigParser
# from mcpModules.modules import modulesClass
import uuid
import string
import math
import copy
import time
import subprocess
import shlex
import sys
import lxml.etree as etree
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import databaseFunctions
import multiprocessing 
import traceback
from externals.singleInstance import singleinstance
from archivematicaFunctions import unicodeToStr

global countOfCreateUnitAndJobChainThreaded
countOfCreateUnitAndJobChainThreaded = 0

config = ConfigParser.SafeConfigParser({'MCPArchivematicaServerInterface': ""})
config.read("/etc/archivematica/MCPServer/serverConfig.conf")

# archivematicaRD = replacementDics(config)

#time to sleep to allow db to be updated with the new location of a SIP
dbWaitSleep = 2
transferDMovedFromCounter = multiprocessing.Value('i', 0) 

configs = []
jobsAwaitingApproval = []
jobsQueue = [] #jobs shouldn't remain here long (a few seconds max) before they are turned into tasks (jobs being processed)
jobsBeingProcessed = []
tasksQueue = []
tasksBeingProcessed = []
tasksLock = threading.Lock()
movingDirectoryLock = threading.Lock()
jobsLock = threading.Lock()
watchedDirectories = []
limitTaskThreads = config.getint('Protocol', "limitTaskThreads")
limitTaskThreadsSleep = config.getfloat('Protocol', "limitTaskThreadsSleep")
limitGearmanConnectionsSemaphore = threading.Semaphore(value=config.getint('Protocol', "limitGearmanConnections"))
reservedAsTaskProcessingThreads = config.getint('Protocol', "reservedAsTaskProcessingThreads")
debug = False
stopSignalReceived = False

def isUUID(uuid):
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
    UUID = ""
    path = path.replace(config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1)

    #find UUID on end of SIP path
    uuidLen = -36
    if isUUID(path[uuidLen-1:-1]):
        UUID = path[uuidLen-1:-1]


    if UUID == "":
        #Find it in the database
        sql = """SELECT sipUUID FROM SIPs WHERE currentPath = '""" + MySQLdb.escape_string(path) + "';"
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

def watchDirectories():
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
            if item == ".svn":
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

#if __name__ == '__main__':
#    signal.signal(signal.SIGTERM, signal_handler)
#    signal.signal(signal.SIGINT, signal_handler)

#configs = loadConfigs()
#directoryWatchList = loadDirectoryWatchLlist(configs)
#archivematicaMCPServerListen()


def signal_handler(signalReceived, frame):
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
    global countOfCreateUnitAndJobChainThreaded
    while True:
        dblockstatus = "SQL Lock: Locked"
        if databaseInterface.sqlLock.acquire(False):
            databaseInterface.sqlLock.release()
            dblockstatus = "SQL Lock: Unlocked"
        print "<DEBUG type=\"archivematicaMCP\">", "\tDate Time: ", databaseInterface.getUTCDate(), "\tThreadCount: ", threading.activeCount(), "\tcountOfCreateUnitAndJobChainThreaded", countOfCreateUnitAndJobChainThreaded, dblockstatus, "</DEBUG>"
        time.sleep(60)

def flushOutputs():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(5)

def startTransferD():
    p = multiprocessing.Process(target=transferD.mainWithMovedFromCounter, args=(transferDMovedFromCounter,))
    p.start()
    print >>sys.stderr, "transferD started - PID:", p.pid
    while p.is_alive():
        time.sleep(5)
    print >>sys.stderr, "transferD crashed\n exitCode:", p.exitcode 


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
    elif False: #testing single instance stuff
        while 1:
            print "psudo run"
            time.sleep(3)
    print "This PID: ", si.pid

    if True:
        import getpass
        print "user: ", getpass.getuser()
        os.setuid(333)
    if False:
        t = threading.Thread(target=debugMonitor)
        t.daemon = True
        t.start()
    if True:
        t = threading.Thread(target=flushOutputs)
        t.daemon = True
        t.start()

    cleanupOldDbEntriesOnNewRun()
    watchDirectories()
    #t = threading.Thread(target=startTransferD)
    #t.daemon = True
    #t.start()

    # This is blocking the main thread with the worker loop
    RPCServer.startRPCServer()
