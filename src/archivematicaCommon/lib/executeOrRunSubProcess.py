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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import print_function
import subprocess
import shlex
import uuid
import os
import sys


def launchSubProcess(command, stdIn="", printing=True, arguments=[], env_updates={}):
    """
    Launches a subprocess using ``command``, where ``command`` is either:
    a) a single string containing a commandline statement, or
    b) an array of commands and parameters.

    In the former case, ``command`` is first split via shlex.split() before
    being executed. No subshell will be used in either case; the commands are
    directly execed.

    Keyword arguments:
    stdIn:      A string which will be fed as standard input to the executed
                process, or a file object which will be provided as a stream
                to the process being executed.
                Default is an empty string.
    printing:   Boolean which controls whether the subprocess's output is
                printed to standard output. Default is True.
    arguments:  An array of arguments to pass to ``command``. Note that this is
                only honoured if ``command`` is an array, and will be ignored
                if ``command`` is a string.
    env_updates: Dict of changes to apply to the started process' environment.
    """
    stdError = ""
    stdOut = ""

    try:
        # Split command strings but pass through arrays untouched
        if isinstance(command, basestring):
            command = shlex.split(command)
        else:
            command.extend(arguments)

        my_env = os.environ.copy()
        my_env['PYTHONIOENCODING'] = 'utf-8'
        if 'LANG' not in my_env or not my_env['LANG']:
            my_env['LANG'] = 'en_US.UTF-8'
        if 'LANGUAGE' not in my_env or not my_env['LANGUAGE']:
            my_env['LANGUAGE'] = my_env['LANG']
        my_env.update(env_updates)

        if isinstance(stdIn, basestring):
            stdin_pipe = subprocess.PIPE
            stdin_string = stdIn
        elif isinstance(stdIn, file):
            stdin_pipe = stdIn
            stdin_string = ""
        else:
            raise Exception("stdIn must be a string or a file object")

        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=stdin_pipe, env=my_env)
        stdOut, stdError = p.communicate(input=stdin_string)
        # append the output to stderror and stdout
        if printing:
            print(stdOut)
            print(stdError, file=sys.stderr)
        retcode = p.returncode
    except OSError as ose:
        print("Execution failed:", ose, file=sys.stderr)
        return -1, "Config Error!", ose.__str__()
    except Exception as inst:
        print("Execution failed:", command, file=sys.stderr)
        print(type(inst), file=sys.stderr)     # the exception instance
        print(inst.args, file=sys.stderr)
        return -1, "Execution failed:", command
    return retcode, stdOut, stdError


def createAndRunScript(text, stdIn="", printing=True, arguments=[], env_updates={}):
    # Output the text to a /tmp/ file
    scriptPath = "/tmp/" + uuid.uuid4().__str__()
    FILE = os.open(scriptPath, os.O_WRONLY | os.O_CREAT, 0o770)
    os.write(FILE, text)
    os.close(FILE)
    cmd = [scriptPath]
    cmd.extend(arguments)

    # Run it
    ret = launchSubProcess(cmd, stdIn="", printing=printing,
                           env_updates=env_updates)

    # Remove the temp file
    os.remove(scriptPath)

    return ret


def executeOrRun(type, text, stdIn="", printing=True, arguments=[], env_updates={}):
    """
    Attempts to run the provided command on the shell, with the text of
    "stdIn" passed as standard input if provided. The type parameter
    should be one of the following:

    command:    Runs the argument as a direct command line. In this usage,
                "text" should be a complete commandline statement,
                which will be split with shlex.split(), or an array.
    bashScript, pythonScript:
                Interprets the "text" argument as the source code to either
                a bash or python script, as appropriate. The appropriate
                shebang will be prepended, then the script will be written
                to disk and executed. If the "arguments" parameter is passed,
                they will be appended to the array that is built to be
                passed to subprocess.Popen.
    as_is:      Like the above, except that the provided script is executed
                without modification.

    Keyword arguments:
    stdIn:      A string which will be fed as standard input to the executed process.
                Default is empty.
    printing:   Boolean which controls whether the subprocess's output is
                printed to standard output. Default is True.
    arguments:  An array of arguments to pass to ``command``. Note that this is only
                honoured if ``command`` is an array, and will be ignored if ``command``
                is a string.
    env_updates: Dict of changes to apply to the started process' environment.
    """
    if type == "command":
        return launchSubProcess(text, stdIn=stdIn, printing=printing, arguments=arguments, env_updates=env_updates)
    if type == "bashScript":
        text = "#!/bin/bash\n" + text
        return createAndRunScript(text, stdIn=stdIn, printing=printing, arguments=arguments, env_updates=env_updates)
    if type == "pythonScript":
        text = "#!/usr/bin/env python2\n" + text
        return createAndRunScript(text, stdIn=stdIn, printing=printing, arguments=arguments, env_updates=env_updates)
    if type == "as_is":
        return createAndRunScript(text, stdIn=stdIn, printing=printing, arguments=arguments, env_updates=env_updates)
