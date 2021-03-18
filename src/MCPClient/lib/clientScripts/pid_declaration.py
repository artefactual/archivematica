#!/usr/bin/env python2
# -*- coding: utf8

"""pid_declaration.py

Given an identifiers.json file, supplying third-party persistent identifiers
(PIDS), such as handle (hdl) or doi, identifiers; associate those identifiers
with the objects in the transfer, so be translated to PREMIS objects in the
AIP METS.
"""
from __future__ import unicode_literals
from functools import wraps
import json
import os
import sys

import django

django.setup()

from main.models import Directory, File, SIP

from change_names import change_name


class DeclarePIDsException(Exception):
    """Exception to raise if there's a more fundamental issue with the running
    of this script and we want to exit and stop the workflow from continuing.
    """


class DeclarePIDsExceptionNonCritical(Exception):
    """Exception to raise when we have problems trying to open identifiers.json
    or the file doesn't exist.
    """

    exit_code = 0


class DeclarePIDs(object):
    """Class to wrap PID declaration features and provide some mechanism of
    recording state.
    """

    SIP_IDENTIFIER = "SIP"
    SIP_DIRECTORY = "%SIPDirectory%"

    def __init__(self, job):
        self.job = job
        self.identifier_count = 0
        self.actual_count = 0

    def exit_on_known_exception(func):
        """Decorator to allows us to raise an exception but still exit-zero when
        the exception is cleaner to return than ad-hoc integer values.
        """

        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except (DeclarePIDsExceptionNonCritical) as err:
                return err.exit_code

        return wrapped

    def _fixup_path_input_by_user(self, path):
        """Fix-up paths submitted by a user, e.g. in custom structmap examples
        so that they don't have to anticipate the Archivematica normalization
        process.
        """
        return "{}{}".format(
            self.SIP_DIRECTORY,
            os.path.join("", *[change_name(name) for name in path.split(os.path.sep)]),
        )

    def _log_identifer_to_stdout(self, mdl, identifier_type, identifier):
        """Create a consistent string to log information about our identifiers
        to stdout for the user.
        """
        try:
            if isinstance(mdl, SIP):
                msg = "Identifier {}: {} added for: {}: {}".format(
                    identifier_type,
                    identifier,
                    "SIP",
                    os.path.basename(os.path.split(mdl.currentpath)[0]),
                )
            elif isinstance(mdl, Directory):
                msg = "Identifier {}: {} added for: {}: {}".format(
                    identifier_type,
                    identifier,
                    "Directory",
                    os.path.basename(os.path.split(mdl.currentlocation)[0]),
                )
            else:
                msg = "Identifier {}: {} added for: {}: {}".format(
                    identifier_type,
                    identifier,
                    "File",
                    os.path.basename(mdl.currentlocation),
                )
            self.job.pyprint(msg)
        except KeyError:
            self.job.pyprint(
                "Identifier {}: {} added to {}".format(identifier_type, identifier, mdl)
            )

    def _validate_identifier(self, mdl, id_):
        """Provide some feedback for the user if the identifier information is
        somehow incomplete.
        """
        identifier_type = id_.get("identifierType", None)
        identifier = id_.get("identifier", None)
        if identifier_type is None:
            self.job.pyprint(
                "None value returned for identifier type: {} on object: {}".format(
                    id_, mdl
                ),
                file=sys.stderr,
            )
            return (False,)
        if identifier is None:
            self.job.pyprint(
                "None value returned for identifier: {} on object: {}".format(id_, mdl),
                file=sys.stderr,
            )
            return (False,)
        return identifier_type, identifier

    def _add_identifier_to_model(self, mdl, id_):
        """Add custom identifier to the model we found a match for. We treat
        incomplete information as a warning which then allows the script to
        continue. This behavior will be easy to change if required with further
        usage and greater understanding of this feature.
        """
        identifier_type, identifier = self._validate_identifier(mdl, id_)
        if identifier_type:
            mdl.add_custom_identifier(identifier_type, identifier)
            self._log_identifer_to_stdout(mdl, identifier_type, identifier)
            self.actual_count += 1

    def parse_and_attach_identifiers(self, unit_uuid, json_data):
        """Take our identifiers and add them to the model objects that we want
        them to belong to by the time we create the AIP METS.
        """
        self.identifier_count = len(json_data)
        for file_object in json_data:
            file_path = file_object.get("file")
            identifiers = file_object.get("identifiers", [])
            objects_dir, base_name = os.path.split(file_path)
            if (objects_dir == "objects" or objects_dir == "") and not base_name:
                file_path = self.SIP_IDENTIFIER
            else:
                # Run name normalization to allow us to pair our data with
                # information already in the database.
                file_path = self._fixup_path_input_by_user(file_path)
            for id_ in identifiers:
                if file_path == self.SIP_IDENTIFIER:
                    mdl = SIP.objects.get(uuid=unit_uuid)
                    self._add_identifier_to_model(mdl, id_)
                    continue
                try:
                    mdl = File.objects.get(sip_id=unit_uuid, currentlocation=file_path)
                    self._add_identifier_to_model(mdl, id_)
                    continue
                except File.DoesNotExist:
                    pass
                try:
                    mdl = Directory.objects.get(
                        sip_id=unit_uuid, currentlocation=os.path.join(file_path, "")
                    )
                    self._add_identifier_to_model(mdl, id_)
                except Directory.DoesNotExist:
                    pass
        self.job.pyprint(
            "{} identifiers added for {} objects in the package".format(
                self.actual_count, self.identifier_count
            )
        )

    def _retrieve_identifiers_path(self, unit_uuid, sip_directory):
        """Retrieve a path to the identifiers.json file from the database."""
        try:
            return File.objects.get(
                sip_id=unit_uuid,
                filegrpuse="metadata",
                currentlocation__endswith="identifiers.json",
            ).currentlocation.replace(self.SIP_DIRECTORY, sip_directory)
        except File.DoesNotExist:
            self.job.pyprint("No identifiers.json file found", file=sys.stderr)
            raise DeclarePIDsExceptionNonCritical()

    @exit_on_known_exception
    def pid_declaration(self, unit_uuid, sip_directory):
        """Process an identifiers.json file and add its values to the correct
        models in the database.
        """
        identifiers = self._retrieve_identifiers_path(unit_uuid, sip_directory)
        try:
            with open(identifiers, "r") as identifiers_file:
                json_data = json.load(identifiers_file)
        except (ValueError, IOError) as err:
            raise DeclarePIDsException(
                "Error loading identifiers.json file: {}".format(err)
            )
        self.parse_and_attach_identifiers(unit_uuid, json_data)


def call(jobs):
    """Primary entry point for this script."""
    for job in jobs:
        with job.JobContext():
            try:
                DeclarePIDs(job).pid_declaration(
                    unit_uuid=job.args[1], sip_directory=job.args[2]
                )
            except IndexError as err:
                job.pyprint("Cannot access Job arguments:", err, file=sys.stderr)
