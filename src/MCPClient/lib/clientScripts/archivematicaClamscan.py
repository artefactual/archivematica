#!/usr/bin/env python2

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

from __future__ import print_function

import abc
import argparse
import os
import re
import subprocess
import sys
import uuid

import django
from django.conf import settings as mcpclient_settings

from archivematicaFunctions import cmd_line_arg_to_unicode
from clamd import ClamdUnixSocket, ClamdNetworkSocket
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoEvents
from main.models import Event, File


logger = get_script_logger("archivematica.mcp.client.clamscan")


def clamav_version_parts(ver):
    """Both clamscan and clamd return a version string that looks like the
    following::

        ClamAV 0.99.2/23992/Fri Oct 27 05:04:12 2017

    Given the example above, this function returns a tuple as follows::

        ("ClamAV 0.99.2", "23992/Fri Oct 27 05:04:12 2017")

    Both elements may be None if the matching failed.
    """
    parts = ver.split('/')
    n = len(parts)
    if n == 1:
        version = parts[0]
        if re.match("^ClamAV", version):
            return version, None
    elif n == 3:
        version, defs, date = parts
        return version, '{}/{}'.format(defs, date)
    return None, None


class ScannerBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def scan(self, path):
        """Scan a file and return a tuple of three elements reporting the
        results. These are the three elements expected:
            1. passed (bool)
            2. state (str - "OK", "ERROR", or "FOUND")
            3. details (str - extra info when ERROR or FOUND)
        """

    @abc.abstractproperty
    def version_attrs(self):
        """Obtain the version details. It is expected to return a tuple of two
        elements: ClamAV version number and virus definition version number.
        The implementor can cache the results.
        """

    def program(self):
        return self.PROGRAM

    def version(self):
        return self.version_attrs()[0]

    def virus_definitions(self):
        return self.version_attrs()[1]


class ClamdScanner(ScannerBase):
    PROGRAM = "ClamAV (clamd)"

    def __init__(self):
        self.addr = mcpclient_settings.CLAMAV_SERVER
        self.timeout = mcpclient_settings.CLAMAV_CLIENT_TIMEOUT
        self.stream = not mcpclient_settings.CLAMAV_PASS_BY_REFERENCE
        self.client = self.get_client()

    def scan(self, path):
        if self.stream:
            method_name = 'pass_by_value'
            result_key = 'stream'
        else:
            method_name = 'pass_by_reference'
            result_key = path

        passed, state, details = (False, None, None)
        try:
            result = getattr(self, method_name)(path)
            state, details = result[result_key]
        except Exception as err:
            logger.error('Virus scanning failed: %s', err, exc_info=True)
        else:
            if state == 'OK':
                passed = True
        return passed, state, details

    def version_attrs(self):
        try:
            self._version_attrs
        except AttributeError:
            self._version_attrs = clamav_version_parts(self.client.version())
        return self._version_attrs

    def get_client(self):
        if ':' not in self.addr:
            return ClamdUnixSocket(path=self.addr)
        host, port = self.addr.split(':')
        return ClamdNetworkSocket(
            host=host,
            port=int(port),
            timeout=self.timeout)

    def pass_by_reference(self, path):
        return self.client.scan(path)

    def pass_by_value(self, path):
        return self.client.instream(open(path))


class ClamScanner(ScannerBase):
    PROGRAM = 'ClamAV (clamscan)'
    COMMAND = 'clamscan'

    def _call(self, *args):
        return subprocess.check_output((self.COMMAND,) + args)

    def scan(self, path):
        passed, state, details = (False, 'ERROR', None)
        try:
            self._call(path)
        except subprocess.CalledProcessError as err:
            if err.returncode == 1:
                state = 'FOUND'
            else:
                logger.error('Virus scanning failed: %s', err.output, exc_info=True)
        else:
            passed, state = (True, 'OK')
        return passed, state, details

    def version_attrs(self):
        try:
            self._version_attrs
        except AttributeError:
            try:
                self._version_attrs = clamav_version_parts(self._call('-V'))
            except subprocess.CalledProcessError:
                self._version_attrs = (None, None)
        return self._version_attrs


def file_already_scanned(file_uuid):
    return 0 < Event.objects.filter(
        file_uuid_id=file_uuid,
        event_type='virus check').count()


def record_event(file_uuid, date, scanner, passed):
    if file_uuid == "None":
        return

    event_detail = ''
    if scanner is not None:
        event_detail = 'program="{}"; version="{}"; virusDefinitions="{}"' \
            .format(
                scanner.program(),
                scanner.version(),
                scanner.virus_definitions(),
            )

    outcome = 'Pass' if passed else 'Fail'
    logger.info('Recording new event for file %s (outcome: %s)', file_uuid, outcome)

    insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=str(uuid.uuid4()),
        eventType="virus check",
        eventDateTime=date,
        eventDetail=event_detail,
        eventOutcome=outcome)


def get_parser():
    """ Return a ``Namespace`` with the parsed arguments. """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file_uuid',
        metavar='fileUUID')
    parser.add_argument(
        'path',
        metavar='PATH',
        help='File or directory location')
    parser.add_argument(
        'date',
        metavar='DATE')
    parser.add_argument(
        'task_uuid',
        metavar='taskUUID',
        help='Currently unused, feel free to ignore.')
    return parser


def get_scanner(size):
    """ Return the ClamAV scanner that is more appropiate given the size of the
    file and the threshold setting. The goal is to use ClamScanner instead of
    ClamdScanner because the latter won't take files that are too big. """
    threshold = mcpclient_settings.CLAMAV_CLIENT_THRESHOLD * 1024 * 1024  # Convert to bytes
    if size > threshold:
        return ClamScanner()
    return ClamdScanner()


def get_size(file_uuid, path):
    # We're going to see this happening when files are not part of `objects/`.
    if file_uuid != "None":
        try:
            return File.objects.get(uuid=file_uuid).size
        except File.DoesNotExist:
            pass
    # Our fallback.
    try:
        return os.path.getsize(path)
    except:
        return None


def scan_file(file_uuid, path, date, task_uuid):
    if file_already_scanned(file_uuid):
        logger.info('Virus scan already performed, not running scan again')
        return 0

    scanner, passed = None, False

    try:
        size = get_size(file_uuid, path)
        if not size:
            logger.error('Unexpected file size')
            return 1

        scanner = get_scanner(size)
        logger.info(
            'Using scanner %s (%s - %s)',
            scanner.program(),
            scanner.version(),
            scanner.virus_definitions())

        passed, state, details = scanner.scan(path)
    except:
        logger.error('Unexpected error scanning file %s', path, exc_info=True)
        return 1
    else:
        logger.info('File %s scanned!', path)
        logger.debug('passed=%s state=%s details=%s',
                     passed, state, details)
    finally:
        record_event(file_uuid, date, scanner, passed)

    return 0 if passed else 1


def main(args):
    django.setup()

    parser = get_parser()
    args = parser.parse_args(args)
    kwargs = vars(args)
    kwargs['path'] = cmd_line_arg_to_unicode(kwargs['path'])

    return scan_file(**kwargs)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
