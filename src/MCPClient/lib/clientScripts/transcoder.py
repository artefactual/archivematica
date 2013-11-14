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
import os
import re
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
from archivematicaFunctions import escapeForCommand

# TODO is this needed?  Django models used, but not defined/queried here
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

def toStrFromUnicode(inputString, encoding='utf-8'):
    """Converts to str, if it's unicode input type."""
    if isinstance(inputString, unicode):
        inputString = inputString.encode(encoding)
    return inputString


class Command(object):
    def __init__(self, command, replacement_dict, on_success=None, opts=None):
        self.fpcommand = command
        self.command = command.command
        self.type = command.script_type
        self.output_location = command.output_location
        self.replacement_dict = {}
        self.on_success = on_success
        self.std_out = ""
        self.exit_code = None
        self.opts = opts

        # Enocding stuff for the replacement dict, since it was here before
        for key, value in replacement_dict.iteritems():
            self.replacement_dict[toStrFromUnicode(key)] = toStrFromUnicode(value
                )
        # Add the output location to the replacement dict - for use in
        # verification and event detail commands
        if self.output_location:
            for (key, value) in self.replacement_dict.iteritems():
                self.output_location = self.output_location.replace(key, value)
            self.replacement_dict['%outputLocation%'] = self.output_location

        # Add verification and event detail commands, if they exist
        self.verification_command = None
        if self.fpcommand.verification_command:
            self.verification_command = Command(self.fpcommand.verification_command, self.replacement_dict)

        self.event_detail_command = None
        if self.fpcommand.event_detail_command:
            self.event_detail_command = Command(self.fpcommand.event_detail_command, self.replacement_dict)

    def __str__(self):
        return u"[COMMAND] {}\n\tExecuting: {}\n\tOutput location: {}\n".format(self.fpcommand, self.command, self.verification_command, self.output_location)

    def execute(self, skip_on_success=False):
        """ Execute the the command, and associated verification and event detail commands.

        Returns 0 if all commands succeeded, non-0 if any failed. """
        # For "command" and "bashScript" type delegate tools, e.g.
        # individual commandline statements or bash scripts, we interpolate
        # the necessary values into the script's source
        args = []
        if self.type in ['command', 'bashScript']:
            # For each key replace all instances of the key in the command string
            for key, value in self.replacement_dict.iteritems():
                self.command = self.command.replace(key, escapeForCommand(value) )
        # For other command types, we translate the entries from
        # replacement_dict into GNU-style long options, e.g.
        # [%fileName%, foo] => --file-name=foo
        else:
            for key, value in self.replacement_dict.iteritems():
                optname = re.sub(r'([A-Z]+)', r'-\1', key[1:-1]).lower()
                optvalue = escapeForCommand(value)
                opt = '--{k}={v}'.format(k=optname, v=optvalue)
                args.append(opt)
        print "Command to execute:", self.command
        self.exit_code, self.std_out, std_err = executeOrRun(self.type, self.command, arguments=args, printing=True)
        print 'Command exit code:', self.exit_code
        if self.exit_code == 0 and self.verification_command:
            print "Running verification command", self.verification_command
            self.exit_code = self.verification_command.execute(skip_on_success=True)
            print 'Verification Command exit code:', self.exit_code

        if self.exit_code == 0 and self.event_detail_command:
            print "Running event detail command", self.event_detail_command
            self.event_detail_command.execute(skip_on_success=True)

        # If unsuccesful
        if self.exit_code != 0:
            print >> sys.stderr, "Failed:", self.fpcommand
            print >> sys.stderr, "Standard out:", self.std_out
            print >> sys.stderr, "Standard error:", std_err
        else:
            if (not skip_on_success) and self.on_success:
                self.on_success(self, self.opts, self.replacement_dict)
        return self.exit_code

class CommandLinker(object):
    def __init__(self, fprule, command, replacement_dict, opts, on_success):
        self.fprule = fprule
        self.command = command
        self.replacement_dict = replacement_dict
        self.opts = opts
        self.on_success = on_success
        self.commandObject = Command(self.command, replacement_dict, self.on_success, opts)

    def __str__(self):
        return "[Command Linker] FPRule: {fprule} Command: {co}".format(fprule=self.fprule.uuid, co=self.commandObject)

    def execute(self):
        """ Execute the command, and track the success statistics.

        Returns 0 on success, non-0 on failure. """
        # Track success/failure rates of FP Rules
        self.fprule.count_attempts += 1
        ret = self.commandObject.execute()
        if ret:
            self.fprule.count_not_okay += 1
        else:
            self.fprule.count_okay += 1
        return ret
