#!/usr/bin/env python
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
import io
import os
import shlex
import subprocess
import sys
import tempfile
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from archivematicaFunctions import escape

Arguments = List[str]
Input = Union[str, bytes, io.IOBase]
Environment = Dict[str, str]
Command = Union[str, List[str]]
Result = Tuple[int, str, str]


def launchSubProcess(
    command: Command,
    stdIn: Input = "",
    printing: bool = True,
    arguments: Optional[Arguments] = None,
    env_updates: Optional[Environment] = None,
    capture_output: bool = False,
) -> Result:
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
    capture_output: Whether or not to capture stdout from the subprocess.
                    Defaults to `False`. If `False`, then stdout is never
                    captured and is returned as an empty string; if `True`,
                    then stdout is always captured. The stderr is always
                    captured from the subprocess, regardless of this setting.
                    If `capture_output` is `False`, then that stderr is only
                    returned IF the subprocess has failed, i.e., returned a
                    non-zero exit code.
    """
    if arguments is None:
        arguments = []
    if env_updates is None:
        env_updates = {}
    stdError = ""
    stdOut = ""

    try:
        # Split command strings but pass through arrays untouched
        if isinstance(command, str):
            command = shlex.split(command)
        else:
            command.extend(arguments)

        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        if "LANG" not in my_env or not my_env["LANG"]:
            my_env["LANG"] = "en_US.UTF-8"
        if "LANGUAGE" not in my_env or not my_env["LANGUAGE"]:
            my_env["LANGUAGE"] = my_env["LANG"]
        my_env.update(env_updates)

        if isinstance(stdIn, str):
            stdin_pipe = subprocess.PIPE
            communicate_input = stdIn.encode()
        elif isinstance(stdIn, bytes):
            stdin_pipe = subprocess.PIPE
            communicate_input = stdIn
        elif isinstance(stdIn, io.IOBase):
            stdin_pipe = stdIn.fileno()
            communicate_input = None
        else:
            raise Exception("stdIn must be a string or a file object")
        if capture_output:
            # Capture the stdout and stderr of the subprocess
            p = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=stdin_pipe,
                env=my_env,
            )
            std_out, std_error = p.communicate(input=communicate_input)
            stdOut = escape(std_out)
            stdError = escape(std_error)
        else:
            # Ignore the stdout of the subprocess, capturing only stderr
            with open(os.devnull, "w") as devnull:
                p = subprocess.Popen(
                    command,
                    stdin=stdin_pipe,
                    env=my_env,
                    stdout=devnull,
                    stderr=subprocess.PIPE,
                )
                __, std_error = p.communicate(input=communicate_input)
                stdError = escape(std_error)
        retcode = p.returncode
        # If we are not capturing output and the subprocess has succeeded, set
        # its stderr to the empty string.
        if (not capture_output) and (retcode == 0):
            stdError = ""
        # append the output to stderror and stdout
        if printing:
            print(stdOut)
            print(stdError, file=sys.stderr)
    except OSError as ose:
        print("Execution failed:", ose, file=sys.stderr)
        return -1, "Config Error!", ose.__str__()
    except Exception as inst:
        command_str = " ".join(command)
        print("Execution failed:", command_str, file=sys.stderr)
        print(type(inst), file=sys.stderr)  # the exception instance
        print(inst.args, file=sys.stderr)
        return -1, "Execution failed:", command_str
    return retcode, stdOut, stdError


def createAndRunScript(
    text: Command,
    stdIn: Input = "",
    printing: bool = True,
    arguments: Optional[Arguments] = None,
    env_updates: Optional[Environment] = None,
    capture_output: bool = True,
) -> Result:
    if arguments is None:
        arguments = []
    if env_updates is None:
        env_updates = {}
    # Write script to temporary file and execute it
    with tempfile.NamedTemporaryFile(
        encoding="utf-8", mode="wt", delete=False
    ) as tmpfile:
        os.chmod(tmpfile.name, 0o770)
        if isinstance(text, str):
            tmpfile.write(text)
        else:
            tmpfile.write(" ".join(text))
        tmpfile.close()
        cmd = [tmpfile.name]
        cmd.extend(arguments)

        # Run it
        ret = launchSubProcess(
            cmd,
            stdIn="",
            printing=printing,
            env_updates=env_updates,
            capture_output=capture_output,
        )
        os.unlink(tmpfile.name)
    return ret


def executeOrRun(
    type: str,
    text: Command,
    stdIn: Input = "",
    printing: bool = True,
    arguments: Optional[Arguments] = None,
    env_updates: Optional[Environment] = None,
    capture_output: bool = True,
) -> Result:
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
    capture_output: Whether or not to capture output for the executed process.
                Default is `True`.
    """
    if arguments is None:
        arguments = []
    if env_updates is None:
        env_updates = {}
    if type == "command":
        return launchSubProcess(
            text,
            stdIn=stdIn,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == "bashScript":
        if not isinstance(text, str):
            raise ValueError("command must be a str")
        text = f"#!/bin/bash\n{text}"
        return createAndRunScript(
            text,
            stdIn=stdIn,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == "pythonScript":
        if not isinstance(text, str):
            raise ValueError("command must be a str")
        text = f"#!/usr/bin/env python\n{text}"
        return createAndRunScript(
            text,
            stdIn=stdIn,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    if type == "as_is":
        return createAndRunScript(
            text,
            stdIn=stdIn,
            printing=printing,
            arguments=arguments,
            env_updates=env_updates,
            capture_output=capture_output,
        )
    raise ValueError(f"unknown type {type}")
