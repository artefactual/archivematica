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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

import subprocess
import shlex
import uuid
import os
import sys

def launchSubProcess(command, stdIn="", printing=True):
    stdError = ""
    stdOut = ""
    #print  >>sys.stderr, command
    try:
        my_env = os.environ
        my_env['PYTHONIOENCODING'] = 'utf-8'
        my_env['LANG'] = 'en_CA.UTF-8'
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=my_env)
        stdOut, stdError = p.communicate(input=stdIn)
        #append the output to stderror and stdout
        if printing:
            print stdOut
            print  >>sys.stderr, stdError
        retcode = p.returncode
    except OSError, ose:
        print >>sys.stderr, "Execution failed:", ose
        return -1, "Config Error!", ose.__str__()
    except Exception  as inst:
        print  >>sys.stderr, "Execution failed:", command
        print >>sys.stderr, type(inst)     # the exception instance
        print >>sys.stderr, inst.args
        return -1, "Execution failed:", command
    return retcode, stdOut, stdError



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
