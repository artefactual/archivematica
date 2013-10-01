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
# @subpackage archivematicaClient
# @author Joseph Perry <joseph@artefactual.com>
import sys
import time

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
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

class CommandQueryFailed(Exception):
    pass

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
        sql = """SELECT fpr_fpcommand.script_type, fpr_fpcommand.verification_command_id, fpr_fpcommand.event_detail_command_id, fpr_fpcommand.command, fpr_fpcommand.output_location, fpr_fpcommand.description, fpr_formatversion.description
        FROM fpr_fpcommand
        LEFT JOIN fpr_formatversion ON fpr_fpcommand.output_format_id = fpr_formatversion.uuid
        WHERE fpr_fpcommand.uuid = '{}';""".format(commandID)
        c, sqlLock = databaseInterface.querySQL(sql)
        if c.rowcount == 0L:
            raise CommandQueryFailed('Zero results retrieved for query: {s}'.format(s=sql))
        # This should be impossible, since we're fetching on fpr_fpcommand.uuid
        elif c.rowcount > 1L:
            raise CommandQueryFailed('More than one result retrieved for query: {s}'.format(s=sql))
        else:
            row = [toStrFromUnicode(r) for r in c.fetchone()]
            ( # Extract all elements from row
                self.type,
                self.verificationCommand,
                self.eventDetailCommand,
                self.command,
                self.outputLocation,
                self.description,
                self.outputFormat,
            ) = row
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
            self.command = self.command.replace( key, escapeForCommand(self.replacementDic[key]) )
            if self.outputLocation:
                self.outputLocation = self.outputLocation.replace( key, self.replacementDic[key] )
        print "Running: ", self
        if self.opts:
            self.opts["prependStdOut"] += "\r\nRunning: \r\n{}".format(self)

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
        sql =  "SELECT command_id FROM fpr_fprule WHERE uuid = '{0}';".format(self.pk)
        rows = databaseInterface.queryAllSQL(sql)
        for row in rows:
            self.command = row[0]
        self.commandObject = Command(str(self.command), replacementDic, self.onSuccess, opts)

    def __str__(self):
        return "[Command Linker]\nPK: {pk}\n{co}".format(pk=self.pk, co=self.commandObject)

    def execute(self):
        # Track success/failure rates of FP Rules
        sql = "UPDATE fpr_fprule SET count_attempts=count_attempts+1 WHERE uuid='{}';".format(self.pk)
        databaseInterface.runSQL(sql)
        ret = self.commandObject.execute()
        if ret:
            column = "count_not_okay"
        else:
            column = "count_okay"
        sql = "UPDATE fpr_fprule SET {column} = {column}+1 WHERE uuid='{pk}';".format(column=column, pk=self.pk)
        databaseInterface.runSQL(sql)
        return ret

