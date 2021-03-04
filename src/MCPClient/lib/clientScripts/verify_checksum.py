# -*- coding: utf-8 -*-

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

"""Verify Checksum Job

Archivematica wraps the hashsum utility to verify checksums provided to the
system as part of a transfer, e.g. checksum.md5 in the transfer metadata
folder. We wrap this coreutils utility by using a Hashsum class which enables
us to easily call each of the tools packaged against its different algorithms:

    * MD5
    * SHA1
    * SHA256
    * SHA512
"""

from __future__ import print_function, unicode_literals

import datetime
import os
import subprocess
import sys
import uuid

import django
import scandir
from django.db import transaction

django.setup()
from archivematicaFunctions import strToUnicode
from main.models import Event, File, Transfer

from custom_handlers import get_script_logger


logger = get_script_logger("archivematica.mcp.client.verify_checksum")


class NoHashCommandAvailable(Exception):
    """Provide feedback to the user if the checksum command cannot be found
    for the provided checksum file.
    """


class PREMISFailure(Exception):
    """Provide feedback to the user if there is a problem writing PREMIS event
    information to the database.
    """


class Hashsum(object):
    """Class to capture various functions around calling Hashsum as a mechanism
    for comparing user-supplied checksums in Archivematica.
    """

    # Key-values consisting of a "hash file" specific to a checksum algorithm,
    # and the hashsum command that we want to call against the file.
    HASHFILES_COMMANDS = {
        "checksum.md5": "md5sum",
        "checksum.sha1": "sha1sum",
        "checksum.sha256": "sha256sum",
        "checksum.sha512": "sha512sum",
    }

    OKAY_STRING = ": OK"
    FAIL_STRING = ": FAILED"
    ZERO_STRING = "no properly formatted"
    IMPROPER_STRING = "improperly formatted"
    FAILED_OPEN = ": FAILED open or read"
    EXIT_NON_ZERO = "returned non-zero exit status 1"

    def __init__(self, path, job=print):
        """Initialize an object prepared to invoke a hashsum command on a given
        hash file at a given path and return properties related to that
        invocation to the caller, e.g. to add provenance information to PREMIS
        output.
        """
        try:
            self.job = job
            self.command_called = None
            self.hashfile = path
            self.COMMAND = self.HASHFILES_COMMANDS[os.path.basename(path)]
        except KeyError:
            raise NoHashCommandAvailable()

    def _call(self, *args, **kwargs):
        """Make the call to Python subprocess and record the command being
        called.
        """
        self.command_called = (self.COMMAND,) + args
        return self._decode(
            subprocess.check_output(self.command_called, cwd=kwargs.get("transfer_dir"))
        )

    def count_and_compare_lines(self, objects_dir):
        """Count the number of lines in a checksum file and compare with the
        number of objects being transferred. The requirement of hashsum as
        this microservice job is written is that the mapping is 1:1. There
        isn't space for an empty line at the end of the file.
        """
        lines = self._count_lines(self.hashfile)
        objects = self._count_files(objects_dir)
        if lines == objects:
            return True
        self.job.pyprint(
            "{}: Comparison failed with {} checksum lines and {} "
            "transfer files".format(self.get_ext(self.hashfile), lines, objects),
            file=sys.stderr,
        )
        return False

    def compare_hashes(self, transfer_dir):
        """Compare transfer files with the checksum file provided."""
        objects_dir = os.path.join(transfer_dir, "objects")
        if not self.count_and_compare_lines(objects_dir):
            return 1
        try:
            self._call("-c", "--strict", self.hashfile, transfer_dir=objects_dir)
            return 0
        except subprocess.CalledProcessError as err:
            if self.EXIT_NON_ZERO in str(err):
                warn = "{}: comparison exited with status: {}. Please check the formatting of the checksums or integrity of the files.".format(
                    self.get_ext(self.hashfile), err.returncode
                )
                self.job.pyprint(warn, file=sys.stderr)
            for line in self._decode(err.output):
                if not line:
                    continue
                if line.endswith(self.OKAY_STRING):
                    continue
                if (
                    line.endswith(self.FAIL_STRING)
                    or self.ZERO_STRING in line
                    or self.IMPROPER_STRING in line
                ):
                    self.job.pyprint(
                        "{}: {}".format(self.get_ext(self.hashfile), line),
                        file=sys.stderr,
                    )
                if line.endswith(self.FAILED_OPEN):
                    self.job.pyprint(
                        "{}: {}".format(self.get_ext(self.hashfile), line),
                        file=sys.stderr,
                    )
            return err.returncode

    def version(self):
        """Return version information for the command being called."""
        try:
            return self._call("--version")[0]
        except subprocess.CalledProcessError:
            return self.COMMAND

    def get_command_detail(self):
        """Provide some way for the user to get information out of the class to
        write METS/PREMIS provenance information.
        """
        if not self.command_called:
            err_str = "Unable to retrieve information about the hashsum command called by the script"
            raise PREMISFailure(err_str)
        return 'program="{}"; version="{}"'.format(
            " ".join(self.command_called), self.version()
        )

    @staticmethod
    def _decode(out):
        """Decode string output in Py2 or Py3 and return a list of lines to be
        parsed elsewhere.
        """
        try:
            return str(out, "utf8").split("\n")
        except TypeError:
            return out.decode("utf8").split("\n")

    @staticmethod
    def get_ext(path):
        """Return the extension of the checksum file provided"""
        ext = os.path.splitext(path)[1]
        if not ext:
            return path
        return ext.replace(".", "")

    @staticmethod
    def _count_lines(path):
        """Count the number of lines in a checksum file."""
        count = 0
        with open(path) as hashfile:
            for count, _ in enumerate(hashfile):
                pass
        # Negate zero-based count.
        return count + 1

    @staticmethod
    def _count_files(path):
        """Walk the directories on a given path and count the number of files."""
        return sum([len(files) for _, _, files in scandir.walk(path)])


def get_file_queryset(transfer_uuid):
    """
    Return a queryset for File objects related to the SIP/Transfer.
    """
    file_objs_queryset = File.objects.filter(
        **{"removedtime__isnull": True, "transfer_id": transfer_uuid}
    )
    if not file_objs_queryset.exists():
        err_str = "Unable to find the transfer objects for the SIP: '{}' in the database".format(
            transfer_uuid
        )
        raise PREMISFailure(err_str)
    return file_objs_queryset


def write_premis_event_per_file(file_uuids, transfer_uuid, event_detail):
    """Generate PREMIS events per File object verified in this transfer."""
    event_type = "fixity check"
    event_outcome = "pass"
    events = []
    agents = Transfer.objects.get(uuid=transfer_uuid).agents
    with transaction.atomic():
        for file_obj in file_uuids:
            checksum_event = Event(
                file_uuid=file_obj,
                event_type=event_type,
                event_datetime=datetime.datetime.now(),
                event_outcome=event_outcome,
                event_detail=event_detail,
                event_id=uuid.uuid4(),
            )
            events.append(checksum_event)
        # All the events sit in memory at this point and are then written.
        # We could write this in batches if we need to optimize further.
        Event.objects.bulk_create(events)
        # Adding many-to-many fields with bulk create is awkward, we have to
        # loop through again.
        for event in Event.objects.filter(
            file_uuid__in=[event.file_uuid for event in events]
        ):
            event.agents.add(*agents)


def run_hashsum_commands(job):
    """Run hashsum commands and generate a cumulative return code."""
    transfer_dir = None
    transfer_uuid = None
    try:
        transfer_dir = strToUnicode(job.args[1])
        transfer_uuid = job.args[2]
    except IndexError:
        logger.error("Cannot access expected module arguments: %s", job.args)
        return 1
    ret = 0
    # Create a query-set once so we don't need to generate per each checksum
    # file type.
    file_queryset = get_file_queryset(transfer_uuid)
    for hashfile in Hashsum.HASHFILES_COMMANDS:
        hashsum = None
        hashfilepath = os.path.join(transfer_dir, "metadata", hashfile)
        if os.path.exists(hashfilepath):
            try:
                hashsum = Hashsum(hashfilepath, job)
            except NoHashCommandAvailable:
                job.pyprint(
                    "Nothing to do for {}. No command available.".format(
                        Hashsum.get_ext(hashfilepath)
                    )
                )
                continue
        if hashsum:
            job.pyprint(
                "Comparing transfer checksums with the supplied {} file".format(
                    Hashsum.get_ext(hashfilepath)
                ),
                file=sys.stderr,
            )
            result = hashsum.compare_hashes(transfer_dir=transfer_dir)
            # Add to PREMIS on success only.
            if result == 0:
                job.pyprint("{}: Comparison was OK".format(Hashsum.get_ext(hashfile)))
                write_premis_event_per_file(
                    file_uuids=file_queryset,
                    transfer_uuid=transfer_uuid,
                    event_detail=hashsum.get_command_detail(),
                )
                continue
            ret += result
    return ret


def call(jobs):
    """Primary entry point for MCP Client script."""
    for job in jobs:
        with job.JobContext(logger=logger):
            job.set_status(run_hashsum_commands(job))
