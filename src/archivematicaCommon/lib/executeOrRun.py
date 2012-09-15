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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import shlex
import uuid
import os
import threading
from twisted.internet import protocol as twistedProtocol
from twisted.internet import reactor

import re

class twistedLaunchSubProcess(twistedProtocol.ProcessProtocol):
    def __init__(self, doneLock, stdIn="", printing=True):
        self.stdIn = stdIn
        self.stdOut = ""
        self.stdError = ""
        self.doneLock = doneLock
        self.exitCode = None
        self.printing = printing

    def connectionMade(self):
        if self.stdIn:
            self.transport.write(self.stdIn)
        self.transport.closeStdin() # tell them we're done
    def outReceived(self, stdOut):
        if self.printing:
            print stdOut
        self.stdOut = self.stdOut + stdOut

    def errReceived(self, stdError):
        if self.printing:
            print stdError
        self.stdError = self.stdError + stdError

    def processEnded(self, reason):
        self.exitCode = reason.value.exitCode
        self.doneLock.release()


def launchSubProcess(command, stdIn="", printing=True):
    doneLock = threading.Lock()
    doneLock.acquire()
    tsp = twistedLaunchSubProcess(doneLock, stdIn, printing)
    commands = shlex.split(command)
    reactor.spawnProcess(tsp, commands[0], commands, {})
    if not reactor._started:
        reactor.run()
    doneLock.acquire()
    return tsp.exitCode, tsp.stdOut, tsp.stdError



def createAndRunScript(text, stdIn="", printing=True):
    #output the text to a /tmp/ file
    scriptPath = "/tmp/" + uuid.uuid4().__str__()
    FILE = os.open(scriptPath, os.O_WRONLY | os.O_CREAT, 0770)
    os.write(FILE, text)
    os.close(FILE)

    #run it
    ret = launchSubProcess(scriptPath, stdIn="", printing=True)

    #remove the temp file
    os.remove(scriptPath)

    return ret



def executeOrRun(type, text, stdIn="", printing=True):
    if type == "command":
        return launchSubProcess(text, stdIn=stdIn, printing=printing)
    if type == "bashScript":
        text = "#!/bin/bash\n" + text
        return createAndRunScript(text, stdIn=stdIn, printing=printing)
    if type == "pythonScript":
        text = "#!/usr/bin/python -OO\n" + text
        return createAndRunScript(text, stdIn=stdIn, printing=printing)
