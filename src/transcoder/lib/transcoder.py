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
# @subpackage transcoder
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

fileTitle = ""
fileExtension = ""
fileDirectory = ""
fileFullName = ""
def setFileIn(fileIn=sys.argv[1]):
    global fileTitle
    global fileExtension
    global fileDirectory
    global fileFullName
    #get file name and extension
    s = fileIn
    #get indexes for python string array
    #index of next char after last /
    x1 = s.rfind('/')+1
    #index of last .
    x2 = s.rfind('.')
    #index of next char after last .
    x2mod = x2+1
    #length of s
    sLen = len(s)

    if x2 < x1:
        x2mod = 0


    fileDirectory = os.path.dirname(s) + "/"
    if x2mod != 0:
        fileExtension = s[x2mod:sLen]
        fileTitle = s[x1:x2]
        fileFullName = fileDirectory + fileTitle + "." + fileExtension
    else:
        #print "No file extension!"
        fileExtension = ""
        fileTitle = s[x1:sLen]
        fileFullName = fileDirectory + fileTitle

    #print "fileTitle", fileTitle
    #print "fileExtension", fileExtension
    #print "fileDirectory", fileDirectory
    #print "fileFullName", fileFullName


setFileIn()

commandObjects = {}
groupObjects = {}
commandLinkerObjects = {}

global onSusccess
onSuccess=None #pointer to a function to call once a command completes successfully
global replacementDic
replacementDic = {}
identifyCommands=None

def toStrFromUnicode(inputString, encoding='utf-8'):
    """Converts to str, if it's unicode input type."""
    if isinstance(inputString, unicode):
        inputString = inputString.encode('utf-8')
    return inputString


class Command:
    def __init__(self, commandID):
        self.pk = commandID
        self.stdOut = ""
        self.stdErr = ""
        self.exitCode=None
        self.failedCount=0
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
            self.verificationCommand = Command(self.verificationCommand)
            self.verificationCommand.command = self.verificationCommand.command.replace("%outputLocation%", self.outputLocation)

        if self.eventDetailCommand:
            self.eventDetailCommand = Command(self.eventDetailCommand)
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

        #print self.__str__()

        #Do a dictionary replacement.
        #Replace replacement strings
        global replacementDic

        #for each key replace all instances of the key in the command string
        for key, value in replacementDic.iteritems():
            key = toStrFromUnicode(key)
            replacementDic[key] = toStrFromUnicode(value)
            #self.outputLocation = toStrFromUnicode(self.outputLocation)
            #self.command = self.command.replace ( key, quote(replacementDic[key]) )
            self.command = self.command.replace( key, escapeForCommand(replacementDic[key]) )
            if self.outputLocation:
                self.outputLocation = self.outputLocation.replace( key, replacementDic[key] )
        print "Running: "
        print self.__str__()

        self.exitCode, self.stdOut, self.stdError = executeOrRun(self.type, self.command)


        if (not self.exitCode) and self.verificationCommand:
            print
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
            global onSuccess
            #uncommenting these floods the buffers with ffmpeg
            #print self.stdOut
            #print self.stdError
            if (not skipOnSuccess) and onSuccess:
                onSuccess(self)
        return self.exitCode

class CommandLinker:
    def __init__(self, commandLinker):
        self.pk, self.command, self.group = commandLinker
        if self.command in commandObjects:
            self.commandObject = commandObjects[self.command]
        else:
            co =Command(self.command.__str__())
            self.commandObject = co
            commandObjects[self.command] = co

        if self.group in groupObjects:
            self.groupObject = groupObjects[self.group]
            groupObjects[self.group].members.append(self)
        else:
            go =Group(self.group, [self])
            self.groupObject = go
            groupObjects[self.group] = go

    def __str__(self):
        return "[Command Linker]\n" + \
        "PK: " + self.pk.__str__() + "\n" + \
        self.commandObject.__str__()

    def execute(self):
        sql = "UPDATE CommandRelationships SET countAttempts=countAttempts+1 WHERE pk=" + self.pk.__str__() + ";"
        databaseInterface.runSQL(sql)
        if self.commandObject.exitCode != None:
            if self.commandObject.exitCode:
                column = "countNotOK"
            else:
                column = "countOK"
            sql = "UPDATE CommandRelationships SET " + column + "=" + column + "+1 WHERE pk=" + self.pk.__str__() + ";"
            databaseInterface.runSQL(sql)
            return self.commandObject.exitCode
        else:
            ret = self.commandObject.execute()
            if ret:
                column = "countNotOK"
            else:
                column = "countOK"
            sql = "UPDATE CommandRelationships SET " + column + "=" + column + "+1 WHERE pk=" + self.pk.__str__() + ";"
            databaseInterface.runSQL(sql)
            return ret


class Group:
    def __init__(self, pk, members=[]):
        self.pk = pk
        self.members = members

    def __str__(self):
        members = ""
        for m in self.members:
            members += m.__str__() + "\n"
        return "[GROUP]\n" + \
        "PK: " + self.pk.__str__() + "\n" + \
        members


def main(fileName):
    #determin the pk's of the Command Linkers
    cls = identifyCommands(fileName)

    if cls == []:
        print "Nothing to do"
        return 0

    #Create the groups and command objects for the Command Linkers
    for c in cls:
        cl = CommandLinker(c)
        pk, commandPK, groupPK = c
        commandLinkerObjects[pk] = cl

    #execute
    #Execute everything in the groups above zero
    #exit code/success is checked below - at leat one must be successful
    for g in groupObjects:
        if (g > 0 or g < LowerEndMainGroupMax) and len(groupObjects[g]):
            for group in groupObjects[g]:
                for cl in group.members:
                    cl.execute()
    
    #groups zero to lowerEndMainGroupMax are the main groups
    #Everything in the group must be successful, or it tries to execute the next group (decrement)
    #quit -1 if no main group is successful
    mainGroup = 0
    while True :
        if mainGroup in groupObjects:
            combinedExitCode = 0
            for cl in groupObjects[mainGroup].members:
                cl.execute()
                combinedExitCode += math.fabs(cl.commandObject.exitCode)
            if len(groupObjects[mainGroup].members) > 0 and combinedExitCode == 0:
                break
        if mainGroup == LowerEndMainGroupMax:
            quit(-1)
        mainGroup = mainGroup - 1

    #these are executed above.
    #look for problems
    for g in groupObjects:
        #Groups that require at least one good one.
        if g > 0:
            exitCode=-1
            for cl in groupObjects[g].members:
                if cl.commandObject.exitCode == 0:
                    exitCode = 0
                    break
            if exit:
                quit(exitCode)
        #group that require all good ones
        if g == mainGroup:
            exitCode=0
            for cl in groupObjects[g].members:
                if cl.commandObject.exitCode != 0:
                    exitCode = -1
                    break
            if exit:
                quit(exitCode)
    quit(0)
