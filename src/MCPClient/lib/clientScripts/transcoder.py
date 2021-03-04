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
# @subpackage archivematicaClient

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun

# dashboard
from django.db.models import F
from django.utils import six


def toStrFromUnicode(inputString, encoding="utf-8"):
    """Converts to str, if it's unicode input type."""
    if isinstance(inputString, six.string_types):
        inputString = inputString.encode(encoding)
    return inputString


class Command(object):
    def __init__(self, job, command, replacement_dict, on_success=None, opts=None):
        self.fpcommand = command
        self.command = command.command
        self.type = command.script_type
        self.output_location = command.output_location
        self.replacement_dict = replacement_dict
        self.on_success = on_success
        self.std_out = ""
        self.exit_code = None
        self.opts = opts
        self.job = job

        # Add the output location to the replacement dict - for use in
        # verification and event detail commands
        if self.output_location:
            self.output_location = self.replacement_dict.replace(self.output_location)[
                0
            ]
            self.replacement_dict["%outputLocation%"] = self.output_location

        # Add verification and event detail commands, if they exist
        self.verification_command = None
        if self.fpcommand.verification_command:
            self.verification_command = Command(
                self.job, self.fpcommand.verification_command, self.replacement_dict
            )

        self.event_detail_command = None
        if self.fpcommand.event_detail_command:
            self.event_detail_command = Command(
                self.job, self.fpcommand.event_detail_command, self.replacement_dict
            )

    def __str__(self):
        return u"[COMMAND] {}\n\tExecuting: {}\n\tCommand: {}\n\tOutput location: {}\n".format(
            self.fpcommand,
            self.command,
            self.verification_command,
            self.output_location,
        )

    def execute(self, skip_on_success=False):
        """Execute the the command, and associated verification and event detail commands.

        Returns 0 if all commands succeeded, non-0 if any failed."""
        # For "command" and "bashScript" type delegate tools, e.g.
        # individual commandline statements or bash scripts, we interpolate
        # the necessary values into the script's source
        args = []
        if self.type in ["command", "bashScript"]:
            self.command = self.replacement_dict.replace(self.command)[0]
        # For other command types, we translate the entries from
        # replacement_dict into GNU-style long options, e.g.
        # [%fileName%, foo] => --file-name=foo
        else:
            args = self.replacement_dict.to_gnu_options()
        self.job.print_output("Command to execute:", self.command)
        self.job.print_output("-----")
        self.job.print_output("Command stdout:")
        self.exit_code, self.std_out, std_err = executeOrRun(
            self.type, self.command, arguments=args, printing=True, capture_output=True
        )
        self.job.write_output(self.std_out)
        self.job.write_error(std_err)
        self.job.print_output("-----")
        self.job.print_output("Command exit code:", self.exit_code)
        if self.exit_code == 0 and self.verification_command:
            self.job.print_output(
                "Running verification command", self.verification_command
            )
            self.job.print_output("-----")
            self.job.print_output("Command stdout:")
            self.exit_code = self.verification_command.execute(skip_on_success=True)
            self.job.print_output("-----")
            self.job.print_output("Verification Command exit code:", self.exit_code)

        if self.exit_code == 0 and self.event_detail_command:
            self.job.print_output(
                "Running event detail command", self.event_detail_command
            )
            self.event_detail_command.execute(skip_on_success=True)

        # If unsuccesful
        if self.exit_code != 0:
            self.job.print_error("Failed:", self.fpcommand)
            self.job.print_error("Standard out:", self.std_out)
            self.job.print_error("Standard error:", std_err)
        else:
            if (not skip_on_success) and self.on_success:
                self.on_success(self, self.opts, self.replacement_dict)
        return self.exit_code


class CommandLinker(object):
    def __init__(self, job, fprule, command, replacement_dict, opts, on_success):
        self.fprule = fprule
        self.command = command
        self.replacement_dict = replacement_dict
        self.opts = opts
        self.on_success = on_success
        self.commandObject = Command(
            job, self.command, replacement_dict, self.on_success, opts
        )

    def __str__(self):
        return "[Command Linker] FPRule: {fprule} Command: {co}".format(
            fprule=self.fprule.uuid, co=self.commandObject
        )

    def execute(self):
        """Execute the command, and track the success statistics.

        Returns 0 on success, non-0 on failure."""
        # Track success/failure rates of FP Rules
        # Use Django's F() to prevent race condition updating the counts
        self.fprule.count_attempts = F("count_attempts") + 1
        ret = self.commandObject.execute()
        if ret:
            self.fprule.count_not_okay = F("count_not_okay") + 1
        else:
            self.fprule.count_okay = F("count_okay") + 1
        self.fprule.save()
        return ret
