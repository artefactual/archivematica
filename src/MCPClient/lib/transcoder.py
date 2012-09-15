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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$
import re
import math
import sys
import os
import time
from pipes import quote
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from fileOperations import updateSizeAndChecksum
from archivematicaFunctions import escapeForCommand
import databaseInterface
LowerEndMainGroupMax = -10

commandObjects = {}
groupObjects = {}
commandLinkerObjects = {}

def toStrFromUnicode(inputString, encoding='utf-8'):
    """Converts to str, if it's unicode input type."""
    if isinstance(inputString, unicode):
        inputString = inputString.encode('utf-8')
    return inputString


class Command:
    def __init__(self, commandID, replacementDic, onSuccess=None, opts=None):
        self.pk = commandID
        self.replacementDic = replacementDic
        self.onSuccess = onSuccess
        self.stdOut = ""
        self.stdErr = ""
        self.exitCode=None
        self.failedCount=0
        self.opts = opts
        sql = """SELECT CT.type, C.verificationCommand, C.eventDetailCommand, C.command, C.outputLocation, C.description
        FROM Commands AS C
        JOIN CommandTypes AS CT ON C.commandType = CT.pk
        WHERE C.pk = """ + commandID.__str__() + """
        ;"""
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            rowSTR = []
            for colIndex in range(len(row)):
                rowSTR.append(toStrFromUnicode(row[colIndex])) 
            self.type, \
            self.verificationCommand, \
            self.eventDetailCommand, \
            self.command, \
            self.outputLocation, \
            self.description = \
            rowSTR
            if isinstance(self.command, unicode):
                self.command = self.command.encode('utf-8')
            row = c.fetchone()
        sqlLock.release()
        if self.verificationCommand:
            self.verificationCommand = Command(self.verificationCommand, replacementDic)
            self.verificationCommand.command = self.verificationCommand.command.replace("%outputLocation%", self.outputLocation)

        if self.eventDetailCommand:
            self.eventDetailCommand = Command(self.eventDetailCommand, replacementDic)
            self.eventDetailCommand.command = self.eventDetailCommand.command.replace("%outputLocation%", self.outputLocation)

    def __str__(self):
        if self.verificationCommand:
            return "[COMMAND]\n" + \
            "PK: " + self.pk.__str__() + "\n" + \
            "Type: " + self.type.__str__() + "\n" + \
            "command: " + self.command.__str__() + "\n" + \
            "description: " + self.description.__str__() + "\n" + \
            "outputLocation: " + self.outputLocation.__str__() + "\n" + \
            "verificationCommand: " + self.verificationCommand.pk.__str__()
        else:
            return "[COMMAND]\n" + \
            "PK: " + self.pk.__str__() + "\n" + \
            "Type: " + self.type.__str__() + "\n" + \
            "command: " + self.command.__str__() + "\n" + \
            "description: " + self.description.__str__() + "\n" + \
            "outputLocation: " + self.outputLocation.__str__() + "\n" + \
            "verificationCommand: " + self.verificationCommand.__str__()

    def execute(self, skipOnSuccess=False):
        #for each key replace all instances of the key in the command string
        for key, value in self.replacementDic.iteritems():
            key = toStrFromUnicode(key)
            self.replacementDic[key] = toStrFromUnicode(value)
            #self.outputLocation = toStrFromUnicode(self.outputLocation)
            #self.command = self.command.replace ( key, quote(replacementDic[key]) )
            self.command = self.command.replace( key, escapeForCommand(self.replacementDic[key]) )
            if self.outputLocation:
                self.outputLocation = self.outputLocation.replace( key, self.replacementDic[key] )
        print "Running: "
        selfstr = self.__str__()
        print selfstr
        if self.opts:
            self.opts["prependStdOut"] += "\r\nRunning: \r\n%s" % (selfstr)

        self.exitCode, self.stdOut, self.stdError = executeOrRun(self.type, self.command)


        if (not self.exitCode) and self.verificationCommand:
            print
            if self.opts:
                self.opts["prependStdOut"] += "\r\n"
            self.exitCode = self.verificationCommand.execute(skipOnSuccess=True)

        if (not self.exitCode) and self.eventDetailCommand:
            self.eventDetailCommand.execute(skipOnSuccess=True)

        #If unsuccesful
        if self.exitCode:
            print >>sys.stderr, "Failed:"
            #print >>sys.stderr, self.__str__()
            print self.stdOut
            print >>sys.stderr, self.stdError
            if False and self.failedCount < 1: #retry count
                self.failedCount= self.failedCount + 1
                time.sleep(2)
                print >>sys.stderr, "retrying, ", self.failedCount
                return self.execute(skipOnSuccess)
        else:
            if (not skipOnSuccess) and self.onSuccess:
                self.onSuccess(self, self.opts, self.replacementDic)
        return self.exitCode

class CommandLinker:
    def __init__(self, commandLinker, replacementDic, opts, onSuccess):
        self.pk = commandLinker
        self.replacementDic = replacementDic
        self.opts = opts
        self.onSuccess = onSuccess
        sql =  "SELECT command FROM CommandRelationships where pk = %s;" % (self.pk.__str__())
        rows = databaseInterface.queryAllSQL(sql)
        if rows:
            for row in rows:
                self.command = row[0]
        self.commandObject = Command(self.command.__str__(), replacementDic, self.onSuccess, opts)

    def __str__(self):
        return "[Command Linker]\n" + \
        "PK: " + self.pk.__str__() + "\n" + \
        self.commandObject.__str__()

    def execute(self):
        sql = "UPDATE CommandRelationships SET countAttempts=countAttempts+1 WHERE pk=" + self.pk.__str__() + ";"
        databaseInterface.runSQL(sql)
        ret = self.commandObject.execute()
        if ret:
            column = "countNotOK"
        else:
            column = "countOK"
        sql = "UPDATE CommandRelationships SET " + column + "=" + column + "+1 WHERE pk=" + self.pk.__str__() + ";"
        databaseInterface.runSQL(sql)
        return ret


