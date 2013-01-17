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

#~DOC~
#
# --- This is the MCP Client---
#It connects to the MCP server, and informs the server of the tasks it can perform.
#The server can send a command (matching one of the tasks) for the client to perform.
#The client will perform that task, and return the exit code and output to the server.
#
#For archivematica 0.9 release. Added integration with the transcoder.
#The server will send the transcoder association pk, and file uuid to run.
#The client is responsible for running the correct command on the file. 

import sys
import os
import shlex
import subprocess

if __name__ == '__main__':
    print sys.executable
    print os.__file__
    print __file__
    print u'\u2019'
    i = 0
    if len(sys.argv) != 2:
        i = 0
    else:
        i = int(sys.argv[1]) + 1
    command = "%s %d" % (__file__, i)
    print i
    if i < 10: 
        stdIn = None
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdOut, stdError = p.communicate(input=stdIn)
        print stdOut
        print >>sys.stderr, stdError 
    