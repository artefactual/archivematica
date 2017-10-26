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
import collections
import hashlib
import locale
import os
import re

from main.models import DashboardSetting


REQUIRED_DIRECTORIES = [
    "logs",
    "logs/fileMeta",
    "metadata",
    "metadata/submissionDocumentation",
    "objects",
]

OPTIONAL_FILES = [
    "processingMCP.xml",
]

MANUAL_NORMALIZATION_DIRECTORIES = [
    "objects/manualNormalization/access",
    "objects/manualNormalization/preservation",
]


def get_setting(setting, default=''):
    try:
        return DashboardSetting.objects.get(name=setting).value
    except DashboardSetting.DoesNotExist:
        return default


def get_dashboard_uuid():
    return get_setting('dashboard_uuid', default=None)


class OrderedListsDict(collections.OrderedDict):
    """
    OrderedDict where all keys are lists, and elements are appended automatically.
    """

    def __setitem__(self, key, value):
        # When inserting, insert into a list of items with the same key
        try:
            self[key]
        except KeyError:
            super(OrderedListsDict, self).__setitem__(key, [])
        self[key].append(value)


def unicodeToStr(string):
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string


def strToUnicode(string, obstinate=False):
    if isinstance(string, str):
        try:
            string = string.decode('utf8')
        except UnicodeDecodeError:
            if obstinate:
                # Obstinately get a Unicode instance by replacing
                # indecipherable bytes.
                string = string.decode('utf8', 'replace')
            else:
                raise
    return string


def get_locale_encoding():
    default = 'UTF-8'
    try:
        return locale.getdefaultlocale()[1] or default
    except IndexError:
        return default


def cmd_line_arg_to_unicode(cmd_line_arg):
    """Decode a command-line argument (bytestring, type ``str``) to Unicode
    (type ``unicode``) by decoding it using the default system encoding (if
    retrievable) or UTF-8 otherwise.
    """
    try:
        return cmd_line_arg.decode(get_locale_encoding())
    except (LookupError, UnicodeDecodeError):
        return cmd_line_arg


def getTagged(root, tag):
    ret = []
    for element in root:
        if element.tag == tag:
            ret.append(element)
    return ret


def escapeForCommand(string):
    ret = string
    if isinstance(ret, basestring):
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace("\"", "\\\"")
        ret = ret.replace("`", "\`")
        # ret = ret.replace("'", "\\'")
        # ret = ret.replace("$", "\\$")
    return ret

# This replaces non-unicode characters with a replacement character,
# and is primarily used for arbitrary strings (e.g. filenames, paths)
# that might not be valid unicode to begin with.


def escape(string):
    if isinstance(string, str):
        string = string.decode('utf-8', errors='replace')
    return string


# Normalize non-DC CONTENTdm metadata element names to match those used
# in transfer's metadata.csv files.
def normalizeNonDcElementName(string):
    # Convert non-alphanumerics to _, remove extra _ from ends of string.
    normalizedString = re.sub(r"\W+", '_', string)
    normalizedString = normalizedString.strip('_')
    # Lower case string.
    normalizedString = normalizedString.lower()
    return normalizedString


def get_file_checksum(filename, algorithm='sha256'):
    """
    Perform a checksum on the specified file.

    This function reads in files incrementally to avoid memory exhaustion.
    See: http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python

    :param filename: The path to the file we want to check
    :param algorithm: Which algorithm to use for hashing, e.g. 'md5'
    :return: Returns a checksum string for the specified file.
    """
    h = hashlib.new(algorithm)

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * h.block_size), b''):
            h.update(chunk)

    return h.hexdigest()


def find_metadata_files(sip_path, filename, only_transfers=False):
    """
    Check the SIP and transfer metadata directories for filename.

    Helper function to collect all of a particular metadata file (e.g. metadata.csv) in a SIP.

    SIP-level files will be at the end of the list, if they exist.

    :param sip_path: Path of the SIP to check
    :param filename: Name of the metadata file to search for
    :param only_transfers: True if it should only look at Transfer metadata, False if it should look at SIP metadata too.
    :return: List of full paths to instances of filename
    """
    paths = []
    # Check transfers
    transfers_md_path = os.path.join(sip_path, 'objects', 'metadata', 'transfers')
    try:
        transfers = os.listdir(transfers_md_path)
    except OSError:
        transfers = []
    for transfer in transfers:
        path = os.path.join(transfers_md_path, transfer, filename)
        if os.path.isfile(path):
            paths.append(path)
    # Check SIP metadata dir
    if not only_transfers:
        path = os.path.join(sip_path, 'objects', 'metadata', filename)
        if os.path.isfile(path):
            paths.append(path)
    return paths


def create_directories(directories, basepath='', printing=False):
    for directory in directories:
        dir_path = os.path.join(basepath, directory)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            if printing:
                print('Creating directory', dir_path)


def create_structured_directory(basepath, manual_normalization=False, printing=False):
    create_directories(REQUIRED_DIRECTORIES, basepath=basepath, printing=printing)
    if manual_normalization:
        create_directories(MANUAL_NORMALIZATION_DIRECTORIES, basepath=basepath, printing=printing)
