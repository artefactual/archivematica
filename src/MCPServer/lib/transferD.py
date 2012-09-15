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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#Related Docs
# http://pyinotify.sourceforge.net/doc-v07/index.html
# http://code.google.com/p/archivematica/source/browse/trunk/src/transfer/lib/transferD.py?r=1656

#Variables to move to config file


#imports
import pyinotify
import uuid
import MySQLdb
import sys
import os
import copy
import threading
import time

import archivematicaMCP
from unitTransfer import unitTransfer
from unitSIP import unitSIP

completedTransfersDirectory = "/var/archivematica/sharedDirectory/watchedDirectories/SIPCreation/completedTransfers/"
sipCreationDirectory = "/var/archivematica/sharedDirectory/watchedDirectories/SIPCreation/SIPsUnderConstruction/"


sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from databaseFunctions import fileWasRemoved
from externals.singleInstance import singleinstance

#Local Variables
mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | pyinotify.IN_DELETE | pyinotify.IN_MOVE_SELF | pyinotify.IN_DELETE_SELF
#wm = pyinotify.WatchManager()
movedFrom = {} #cookie
global movedFromCount
movedFromCount = 0
movedFromLock = threading.Lock()

def timerExpired(event, utcDate):
    global movedFromCount
    movedFromLock.acquire()
    if event.cookie in movedFrom:
        #remove it from the list of unfound moves
        movedFromPath, filesMoved, timer = movedFrom.pop(event.cookie)
        movedFromCount.value = movedFromCount.value - 1
        movedFromLock.release()
        for fileUUID, oldLocation in filesMoved:
            fileWasRemoved(fileUUID, utcDate = utcDate, eventOutcomeDetailNote = "removed from: " + oldLocation)
    else:
        movedFromLock.release()

class SIPWatch(pyinotify.ProcessEvent):
    def __init__(self, unit, wm):
        self.unit=unit
        self.wm = wm
    #if a file is moved in, look for a cookie to claim
        #if there isn't one - error
        #error. No adding files to a sip in this manner.
    #else
        #Update the file to be linked to this SIP

    #if the SIP is moved/removed
        #???

    #if a file is moved in, look for a cookie to claim
    def process_IN_MOVED_TO(self, event):
        global movedFromCount
        t = threading.Thread(target=self.threaded_process_IN_MOVED_TO, args=(event,))
        t.daemon = True
        t.start()

    def threaded_process_IN_MOVED_TO(self, event):
        time.sleep(archivematicaMCP.config.getint('MCPServer', "waitToActOnMoves"))
        #print event
        #print "SIP IN_MOVED_TO"
        movedFromLock.acquire()
        if event.cookie not in movedFrom:
            #if there isn't one - error
            #print event.cookie, movedFrom
            #print >>sys.stderr, "#error. No adding files to a sip in this manner."
            movedFromLock.release()
            return

        #remove it from the list of unfound moves
        movedFromPath, filesMoved, timer = movedFrom.pop(event.cookie)
        movedFromCount.value = movedFromCount.value - 1
        movedFromLock.release()

        movedToPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%SIPDirectory%", 1)
        for fileUUID, oldLocation in filesMoved:
            newFilePath = oldLocation.replace(movedFromPath, movedToPath, 1)
            #print "Moved: ", oldLocation, "-> (" + self.unit.UUID + ")" + newFilePath
            databaseInterface.runSQL("UPDATE Files " + \
                "SET currentLocation='" + newFilePath +  "', " + \
                "Files.sipUUID = '" + self.unit.UUID + "' " \
                "WHERE fileUUID='" + fileUUID + "'" )

    def process_IN_MOVED_FROM(self, event):
        global movedFromCount
        #print event
        #print "SIP IN_MOVED_FROM"
        #Wait for a moved to, and if one doesn't occur, consider it moved outside of the system.

        #print "unit current path: ", self.unit.currentPath
        movedFromPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%SIPDirectory%", 1)
        filesMoved = []
        sql = """SELECT fileUUID, currentLocation FROM Files WHERE sipUUID = '""" + self.unit.UUID + "' AND removedTime = 0 AND currentLocation LIKE '" + MySQLdb.escape_string(movedFromPath).replace("%", "\%") + "%';"
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            #print row
            filesMoved.append(row)
            row = c.fetchone()
        sqlLock.release()

        movedFromLock.acquire()
        utcDate = databaseInterface.getUTCDate()
        timer = threading.Timer(archivematicaMCP.config.getint('MCPServer', "delayTimer"), timerExpired, args=[event, utcDate], kwargs={})
        movedFrom[event.cookie] = (movedFromPath, filesMoved, timer)
        movedFromCount.value = movedFromCount.value + 1
        movedFromLock.release()

        #create timer to check if it's claimed by a move to
        timer.start()


    def process_IN_DELETE(self, event):
        #print event
        #print "SIP IN_DELETE"
        #Wait for a moved to, and if one doesn't occur, consider it moved outside of the system.

        movedFromPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%SIPDirectory%", 1)
        filesMoved = []
        sql = """SELECT fileUUID, currentLocation FROM Files WHERE sipUUID = '""" + self.unit.UUID + "' AND removedTime = 0 AND currentLocation LIKE '" + MySQLdb.escape_string(movedFromPath).replace("%", "\%") + "%';"
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            filesMoved.append(row)
            row = c.fetchone()
        sqlLock.release()
        for fileUUID, currentLocation in filesMoved:
            fileWasRemoved(fileUUID, eventOutcomeDetailNote = "removed from: " + currentLocation)

        if event.pathname + "/" ==  self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1):
            #print "stopped notifier for: ", self.unit.currentPath
            self.notifier.stop()

    def process_IN_MOVE_SELF(self, event):
        #print event
        #print "SIP IN_MOVE_SELF"
        path = event.pathname
        wdrm = [event.wd]
        if path.endswith("-unknown-path"):
            recrm = path[:path.rfind("-unknown-path")] + "/"
        else:
            recrm = path + "/"
        for key, watch in self.wm.watches.iteritems():
            if watch.path.startswith(recrm):
                wdrm.append(watch.wd)
        #print "Watch directory: ", event.wd, self.wm.get_path(event.wd)
        #print "Removing watch directory: ", event.pathname
        #wd = self.wm.get_wd(event.pathname)
        rr = self.wm.rm_watch(wdrm, rec=False)
        #print "rr: ", rr
        #print self.wm
        #self.notifier.stop()
        if recrm ==  self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1):
            #print "stopped notifier for: ", self.unit.currentPath
            self.notifier.stop()

    def process_IN_DELETE_SELF(self, event):
        if event.pathname + "/" ==  self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1):
            #print "stopped notifier for: ", self.unit.currentPath
            self.notifier.stop()



class transferWatch(pyinotify.ProcessEvent):
    def __init__(self, unit, wm):
        self.unit=unit
        self.wm = wm

    #when a file is moved out, create a cookie for the file, with the file uuid
    #and a timer, so if it isn't claimed, the cookie is removed.
    def process_IN_MOVED_FROM(self, event):
        global movedFromCount
        #print event
        #print "Transfer IN_MOVED_FROM"
        #Wait for a moved to, and if one doesn't occur, consider it moved outside of the system.


        movedFromPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%transferDirectory%", 1)
        filesMoved = []
        sql = """SELECT fileUUID, currentLocation FROM Files WHERE transferUUID = '""" + self.unit.UUID + "' AND removedTime = 0 AND currentLocation LIKE '" + MySQLdb.escape_string(movedFromPath).replace("%", "\%") + "%';"
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            #print row
            filesMoved.append(row)
            row = c.fetchone()
        sqlLock.release()

        movedFromLock.acquire()
        utcDate = databaseInterface.getUTCDate()
        timer = threading.Timer(archivematicaMCP.config.getint('MCPServer', "delayTimer"), timerExpired, args=[event, utcDate], kwargs={})
        movedFrom[event.cookie] = (movedFromPath, filesMoved, timer)
        movedFromCount.value = movedFromCount.value + 1
        movedFromLock.release()

        #create timer to check if it's claimed by a move to
        timer.start()

        #print "Watch directory: ", event.wd, wm.get_path(event.wd)
        #if event.dir:
        #    print "Removing watch directory: ", event.pathname
        #    wd = wm.get_wd(event.pathname)
        #    wm.rm_watch(wd, rec=True)

    #if a file is moved in, look for a cookie to claim
    def process_IN_MOVED_TO(self, event):
        t = threading.Thread(target=self.threaded_process_IN_MOVED_TO, args=(event,))
        t.daemon = True
        t.start()

    def threaded_process_IN_MOVED_TO(self, event):  
        global movedFromCount      
        time.sleep(archivematicaMCP.config.getint('MCPServer', "waitToActOnMoves"))
        #print event
        movedFromLock.acquire()
        if event.cookie not in movedFrom:
            #if there isn't one - error
            print >>sys.stderr, "#error. No adding files to a sip in this manner."
            movedFromLock.release()
            return

        #remove it from the list of unfound moves
        movedFromPath, filesMoved, timer = movedFrom.pop(event.cookie)
        movedFromCount.value = movedFromCount.value - 1
        movedFromLock.release()

        movedToPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%transferDirectory%", 1)
        for fileUUID, oldLocation in filesMoved:
            newFilePath = oldLocation.replace(movedFromPath, movedToPath, 1)
            #print "Moved: ", oldLocation, "-> (" + self.unit.UUID + ")" + newFilePath
            #print "Todo - verify it belongs to this transfer"
            #if it's from this transfer
                #clear the SIP membership
                #update current location

            databaseInterface.runSQL("UPDATE Files " + \
                "SET currentLocation='" + newFilePath +  "', " + \
                "Files.sipUUID = NULL " + \
                "WHERE fileUUID='" + fileUUID + "'" )
            #else
                #error ish - file doesn't belong here
                #update current location & clear SIP

    #if the transfer is moved/removed
        #???

    def process_IN_DELETE(self, event):
        #print event
        #print "Transfer IN_DELETE"
        #Wait for a moved to, and if one doesn't occur, consider it moved outside of the system.

        movedFromPath = os.path.join(event.path, event.name).replace(\
                             self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1), \
                             "%transferDirectory%", 1)
        filesMoved = []
        sql = """SELECT fileUUID, currentLocation FROM Files WHERE transferUUID = '""" + self.unit.UUID + "' AND removedTime = 0 AND currentLocation LIKE '" + MySQLdb.escape_string(movedFromPath).replace("%", "\%") + "%';"
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            filesMoved.append(row)
            row = c.fetchone()
        sqlLock.release()
        for fileUUID, currentLocation in filesMoved:
            fileWasRemoved(fileUUID, eventOutcomeDetailNote = "removed from: " + currentLocation)

    def process_IN_MOVE_SELF(self, event):
        #print event
        #print "Transfer IN_MOVE_SELF"
        path = event.pathname
        wdrm = [event.wd]
        if path.endswith("-unknown-path"):
            recrm = path[:path.rfind("-unknown-path")] + "/"
        else:
            recrm = path + "/"
        for key, watch in self.wm.watches.iteritems():
            if watch.path.startswith(recrm):
                wdrm.append(watch.wd)
        #print "Watch directory: ", event.wd, self.wm.get_path(event.wd)
        #print "Removing watch directory: ", event.pathname
        #wd = self.wm.get_wd(event.pathname)
        rr = self.wm.rm_watch(wdrm, rec=False)
        #print "rr: ", rr
        #print self.wm

        if recrm ==  self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1):
            #print "stopped notifier for: ", self.unit.currentPath
            self.notifier.stop()

    def process_IN_DELETE_SELF(self, event):
        if event.pathname + "/" ==  self.unit.currentPath.replace("%sharedPath%", archivematicaMCP.config.get('MCPServer', "sharedDirectory"), 1):
            #print "stopped notifier for: ", self.unit.currentPath
            self.notifier.stop()


def addWatchForTransfer(path, unit):
    wm = pyinotify.WatchManager()
    w = transferWatch(unit, wm)
    notifier = pyinotify.ThreadedNotifier(wm, w)
    w.notifier = notifier
    wm.add_watch(path, mask, rec=True, auto_add=True)
    notifier.start()
    return notifier

def addWatchForSIP(path, unit):
    wm = pyinotify.WatchManager()
    w = SIPWatch(unit, wm)
    notifier = pyinotify.ThreadedNotifier(wm, w)
    w.notifier = notifier
    wm.add_watch(path, mask, rec=True, auto_add=True)
    notifier.start()
    return notifier

def loadExistingFiles():
    #Transfers
    directory = completedTransfersDirectory
    if not os.path.isdir(directory):
        os.makedirs(directory)
    for item in os.listdir(directory):
        if item == ".svn":
            continue
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            path = path + "/"
            unit = unitTransfer(path)
            addWatchForTransfer(path, unit)

    #SIPS
    directory = sipCreationDirectory
    if not os.path.isdir(directory):
        os.makedirs(directory)
    for item in os.listdir(directory):
        if item == ".svn":
            continue
        path = os.path.join(directory, item)
        if os.path.isdir(path):
            path = path + "/"
            UUID = archivematicaMCP.findOrCreateSipInDB(path)
            unit = unitSIP(path, UUID)
            addWatchForSIP(path, unit)


class SIPCreationWatch(pyinotify.ProcessEvent):
    "watches for new sips/completed transfers"
    def __init__(self):
        self.sips = {}

    def process_IN_CREATE(self, event):
        self.process_IN_MOVED_TO(event)


    def process_IN_MOVED_TO(self, event):
        #time.sleep(archivematicaMCP.dbWaitSleep) #let db be updated by the microservice that moved it.
        #print event
        #print "process_IN_MOVED_TO SIPCreationWatch"
        path = os.path.join(event.path, event.name)
        if not os.path.isdir(path):
            print >>sys.stderr, "Bad path for watching - not a directory: ", path
            return
        if os.path.abspath(event.path) == os.path.abspath(completedTransfersDirectory):
            path = path + "/"
            unit = unitTransfer(path)
            addWatchForTransfer(path, unit)
        elif os.path.abspath(event.path) == os.path.abspath(sipCreationDirectory):
            path = path + "/"
            UUID = archivematicaMCP.findOrCreateSipInDB(path, waitSleep=0)
            unit = unitSIP(path.replace(archivematicaMCP.config.get('MCPServer', "sharedDirectory"), "%sharedPath%", 1), UUID)
            notifier = addWatchForSIP(path, unit)
            self.sips[path[:-1]] = notifier
        else:
            print >>sys.stderr, "Bad path for watching: ", event.path


    #def process_IN_MOVED_FROM(self, event):
    #    print event
    #    if event.pathname in self.sips:
    #        print "stopping watch on: ", event.name
    #        notifier = self.sips.pop(event.pathname)
    #        notifier.stop()

def startWatching():
    wm = pyinotify.WatchManager()
    notifier = pyinotify.ThreadedNotifier(wm, SIPCreationWatch())
    wm.add_watch(completedTransfersDirectory, mask, rec=False, auto_add=False)
    wm.add_watch(sipCreationDirectory, mask, rec=False, auto_add=False)
    notifier.start()
    #notifier.loop()

def main():
    loadExistingFiles()
    startWatching()

def debugMonitor():
    while True:
        dblockstatus = "SQL Lock: Locked"
        if databaseInterface.sqlLock.acquire(False):
            databaseInterface.sqlLock.release()
            dblockstatus = "SQL Lock: Unlocked"
        #print "<DEBUG type=\"transferD\">", "\tDate Time: ", databaseInterface.getUTCDate(), "\tThreadCount: ", threading.activeCount(), "movedFromCount", movedFromCount.value, dblockstatus, "</DEBUG>"
        time.sleep(10)

def mainWithMovedFromCounter(movedFrom):
    global movedFromCount
    si = singleinstance("/tmp/archivematicaMCPTransferDPID")
    if si.alreadyrunning():
        print >>sys.stderr, "Another instance is already running. Killing PID:", si.pid
        si.kill()
    movedFromCount = movedFrom
    main()
    databaseInterface.reconnect()
    debugMonitor()
    

if __name__ == '__main__':
    main()
