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

"""archivematicaFunctions provides various helper functions across the
different Archivematica modules.
"""

from __future__ import print_function
import collections
import hashlib
import locale
import os
import pprint
import re
from uuid import uuid4

from lxml import etree

from main.models import DashboardSetting
from namespaces import NSMAP


REQUIRED_DIRECTORIES = [
    "logs",
    "logs/fileMeta",
    "metadata",
    "metadata/submissionDocumentation",
    "objects",
]

OPTIONAL_FILES = [
    "processingMCP.xml",
    "README.html",
]

MANUAL_NORMALIZATION_DIRECTORIES = [
    "objects/manualNormalization/access",
    "objects/manualNormalization/preservation",
]


def get_setting(setting, default=''):
    """Get Dashboard setting from database model."""
    try:
        return DashboardSetting.objects.get(name=setting).value
    except DashboardSetting.DoesNotExist:
        return default


def get_dashboard_uuid():
    """Get Dashboard uuid via the Dashboard database mode."""
    return get_setting('dashboard_uuid', default=None)


class OrderedListsDict(collections.OrderedDict):
    """
    OrderedDict where all keys are lists, and elements are appended
    automatically.
    """
    def __setitem__(self, key, value):
        # When inserting, insert into a list of items with the same key
        try:
            self[key]
        except KeyError:
            super(OrderedListsDict, self).__setitem__(key, [])
        self[key].append(value)


def unicodeToStr(string):
    """Convert Unicode to string format."""
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string


def strToUnicode(string, obstinate=False):
    """Convert string to Unicode format."""
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
    """Return the default locale of the machine calling this function."""
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
    """Return the XML elements with the given tag argument."""
    ret = []
    for element in root:
        if element.tag == tag:
            ret.append(element)
    return ret


def escapeForCommand(string):
    """Escape special characters in a given string."""
    ret = string
    if isinstance(ret, basestring):
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace("\"", "\\\"")
        ret = ret.replace("`", "\`")
        # ret = ret.replace("'", "\\'")
        # ret = ret.replace("$", "\\$")
    return ret


def escape(string):
    """Replace non-unicode characters with a replacement character. Use this
    primarily for arbitrary strings (e.g. filenames, paths) that might not
    be valid unicode to begin with.
    """
    if isinstance(string, str):
        string = string.decode('utf-8', errors='replace')
    return string


def normalizeNonDcElementName(string):
    """Normalize non-DC CONTENTdm metadata element names to match those used
    in transfer's metadata.csv files.
    """
    # Convert non-alphanumerics to _, remove extra _ from ends of string.
    normalized_string = re.sub(r"\W+", '_', string)
    normalized_string = normalized_string.strip('_')
    # Lower case string.
    normalized_string = normalized_string.lower()
    return normalized_string


def get_file_checksum(filename, algorithm='sha256'):
    """
    Perform a checksum on the specified file.

    This function reads in files incrementally to avoid memory exhaustion.
    See: https://stackoverflow.com/a/4213255

    :param filename: The path to the file we want to check
    :param algorithm: Which algorithm to use for hashing, e.g. 'md5'
    :return: Returns a checksum string for the specified file.
    """
    hash_ = hashlib.new(algorithm)
    with open(filename, 'rb') as file_:
        for chunk in iter(lambda: file_.read(1024 * hash_.block_size), b''):
            hash_.update(chunk)
    return hash_.hexdigest()


def find_metadata_files(sip_path, filename, only_transfers=False):
    """
    Check the SIP and transfer metadata directories for filename.

    Helper function to collect all of a particular metadata file (e.g.
    metadata.csv) in a SIP.

    SIP-level files will be at the end of the list, if they exist.

    :param sip_path: Path of the SIP to check
    :param filename: Name of the metadata file to search for
    :param only_transfers: True if it should only look at Transfer metadata,
                           False if it should look at SIP metadata too.
    :return: List of full paths to instances of filename
    """
    paths = []
    # Check transfer metadata.
    transfers_md_path = os.path.join(sip_path, 'objects',
                                     'metadata', 'transfers')
    try:
        transfers = os.listdir(transfers_md_path)
    except OSError:
        transfers = []
    for transfer in transfers:
        path = os.path.join(transfers_md_path, transfer, filename)
        if os.path.isfile(path):
            paths.append(path)
    # Check the SIP metadata dir.
    if not only_transfers:
        path = os.path.join(sip_path, 'objects', 'metadata', filename)
        if os.path.isfile(path):
            paths.append(path)
    return paths


def create_directories(directories, basepath='',
                       printing=False, printfn=print):
    """Create arbitrary directory structures given an iterable list of directory
    paths.
    """
    for directory in directories:
        dir_path = os.path.join(basepath, directory)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            if printing:
                printfn('Creating directory', dir_path)


def create_structured_directory(basepath,
                                manual_normalization=False,
                                printing=False, printfn=print):
    """Wrapper for create_directories for various structures required by
    Archivematica.
    """
    create_directories(REQUIRED_DIRECTORIES,
                       basepath=basepath,
                       printing=printing,
                       printfn=printfn)
    if manual_normalization:
        create_directories(MANUAL_NORMALIZATION_DIRECTORIES,
                           basepath=basepath,
                           printing=printing,
                           printfn=printfn)


def get_dir_uuids(dir_paths, logger=None, printfn=print):
    """Return a generator of 2-tuples, each containing one of the directory
    paths in ``dir_paths`` and its newly minted UUID. Used by multiple client
    scripts.
    """
    for dir_path in dir_paths:
        dir_uuid = str(uuid4())
        msg = u'Assigning UUID {} to directory path {}'.format(
            dir_uuid, dir_path)
        printfn(msg)
        if logger:
            logger.info(msg)
        yield dir_path, dir_uuid


def format_subdir_path(dir_path, path_prefix_to_repl):
    """Add "/" to end of ``dir_path`` and replace actual root directory
    ``path_prefix_to_repl`` with a placeholder. Used when creating
    ``originallocation`` attributes for ``Directory`` models.
    """
    return os.path.join(dir_path, '').replace(
        path_prefix_to_repl, '%transferDirectory%', 1)


def str2bool(val):
    """'True' is ``True``; aught else is ``False."""
    if val == 'True':
        return True
    return False


NORMATIVE_STRUCTMAP_LABEL = 'Normative Directory Structure'


def div_el_to_dir_paths(div_el, parent='', include=True):
    """Recursively extract the list of filesystem directory paths encoded in
    <mets:div> element ``div_el``.
    """
    paths = []
    path = parent
    dir_name = div_el.get('LABEL')
    if parent == '' and dir_name in ('metadata', 'submissionDocumentation'):
        return []
    if include:
        path = os.path.join(parent, dir_name)
        paths.append(path)
    for sub_div_el in div_el.findall('mets:div[@TYPE="Directory"]', NSMAP):
        paths += div_el_to_dir_paths(sub_div_el, parent=path)
    return paths


def reconstruct_empty_directories(mets_file_path, objects_path, logger=None):
    """Reconstruct in objects/ path ``objects_path`` the empty directories
    documented in METS file ``mets_file_path``.
    :param str mets_file_path: absolute path to an AIP/SIP's METS file.
    :param str objects_path: absolute path to an AIP/SIP's objects/ directory
        on disk.
    :returns None:
    """
    if (not os.path.isfile(mets_file_path) or
            not os.path.isdir(objects_path)):
        if logger:
            logger.info(u'Unable to construct empty directories, either because'
                        ' there is no METS file at {} or because there is no'
                        ' objects/ directory at {}'.format(mets_file_path,
                                                           objects_path))
        return
    doc = etree.parse(mets_file_path, etree.XMLParser(remove_blank_text=True))
    logical_struct_map_el = doc.find(
        'mets:structMap[@TYPE="logical"][@LABEL="{}"]'.format(
            NORMATIVE_STRUCTMAP_LABEL), NSMAP)
    if logical_struct_map_el is None:
        if logger:
            logger.info(u'Unable to locate a logical structMap labelled {}.'
                        ' Aborting attempt to reconstruct empty'
                        ' directories.'.format(NORMATIVE_STRUCTMAP_LABEL))
        return
    root_div_el = logical_struct_map_el.find(
        'mets:div/mets:div[@LABEL="objects"]', NSMAP)
    if root_div_el is None:
        if logger:
            logger.info(u'Unable to locate a logical structMap labelled {}.'
                        ' Aborting attempt to reconstruct empty'
                        ' directories.'.format(NORMATIVE_STRUCTMAP_LABEL))
        return
    paths = div_el_to_dir_paths(root_div_el, include=False)
    if logger:
        logger.info('paths extracted from METS file:')
        logger.info(pprint.pformat(paths))
    for path in paths:
        path = os.path.join(objects_path, path)
        if not os.path.isdir(path):
            os.makedirs(path)
