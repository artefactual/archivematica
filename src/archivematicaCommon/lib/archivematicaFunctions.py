# -*- coding: utf-8 -*-
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
from __future__ import absolute_import, print_function

import base64
import collections
import hashlib
import locale
import os
import pprint
import re
from uuid import uuid4

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from django.apps import apps
import scandir
import six
from lxml import etree
from namespaces import NSMAP, xml_find_premis

from amclient import AMClient

REQUIRED_DIRECTORIES = (
    "logs",
    "logs/fileMeta",
    "metadata",
    "metadata/submissionDocumentation",
    "objects",
)

OPTIONAL_FILES = ("processingMCP.xml", "README.html")

MANUAL_NORMALIZATION_DIRECTORIES = [
    "objects/manualNormalization/access",
    "objects/manualNormalization/preservation",
]

AMCLIENT_ERROR_CODES = (1, 2, 3, 4, -1)

# Package UUID suffix is a single dash followed by a UUID v4 with hyphens.
PACKAGE_UUID_SUFFIX_LENGTH = 37

# Package extension constants here are copied from Storage Service's
# storage_service.common.utils module.
COMPRESS_EXTENSION_7Z = ".7z"
COMPRESS_EXTENSION_BZIP2 = ".bz2"
COMPRESS_EXTENSION_GZIP = ".gz"

COMPRESS_EXTENSIONS = (
    COMPRESS_EXTENSION_7Z,
    COMPRESS_EXTENSION_BZIP2,
    COMPRESS_EXTENSION_GZIP,
)

PACKAGE_EXTENSIONS = (".tar",) + COMPRESS_EXTENSIONS


def get_setting(setting, default=""):
    """Get Dashboard setting from database model."""
    DashboardSetting = apps.get_model(app_label="main", model_name="DashboardSetting")
    try:
        return DashboardSetting.objects.get(name=setting).value
    except DashboardSetting.DoesNotExist:
        return default


def get_dashboard_uuid():
    """Get Dashboard uuid via the Dashboard database mode."""
    return get_setting("dashboard_uuid", default=None)


def setup_amclient():
    """Initialize and return an AMClient instance."""
    client = AMClient(
        ss_api_key=get_setting("storage_service_apikey", ""),
        ss_user_name=get_setting("storage_service_user", ""),
        ss_url=get_setting("storage_service_url", "").rstrip("/"),
    )
    return client


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
    if isinstance(string, six.text_type):
        return six.ensure_str(string, "utf-8")
    return string


def strToUnicode(string, obstinate=False):
    """Convert string to Unicode format."""
    if isinstance(string, six.binary_type):
        try:
            string = string.decode("utf8")
        except UnicodeDecodeError:
            if obstinate:
                # Obstinately get a Unicode instance by replacing
                # indecipherable bytes.
                string = string.decode("utf8", "replace")
            else:
                raise
    return string


def b64encode_string(data):
    return base64.b64encode(data.encode("utf8")).decode("utf8")


def b64decode_string(data):
    return base64.b64decode(data.encode("utf8")).decode("utf8")


def get_locale_encoding():
    """Return the default locale of the machine calling this function."""
    default = "UTF-8"
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
    if isinstance(ret, six.string_types):
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace('"', '\\"')
        ret = ret.replace("`", "\`")
        # ret = ret.replace("'", "\\'")
        # ret = ret.replace("$", "\\$")
    return ret


def escape(string):
    """Replace non-unicode characters with a replacement character. Use this
    primarily for arbitrary strings (e.g. filenames, paths) that might not
    be valid unicode to begin with.
    """
    if isinstance(string, six.binary_type):
        string = string.decode("utf-8", errors="replace")
    return string


def normalizeNonDcElementName(string):
    """Normalize non-DC CONTENTdm metadata element names to match those used
    in transfer's metadata.csv files.
    """
    # Convert non-alphanumerics to _, remove extra _ from ends of string.
    normalized_string = re.sub(r"\W+", "_", string)
    normalized_string = normalized_string.strip("_")
    # Lower case string.
    normalized_string = normalized_string.lower()
    return normalized_string


def get_file_checksum(filename, algorithm="sha256"):
    """
    Perform a checksum on the specified file.

    This function reads in files incrementally to avoid memory exhaustion.
    See: https://stackoverflow.com/a/4213255

    :param filename: The path to the file we want to check
    :param algorithm: Which algorithm to use for hashing, e.g. 'md5'
    :return: Returns a checksum string for the specified file.
    """
    hash_ = hashlib.new(algorithm)
    with open(filename, "rb") as file_:
        for chunk in iter(lambda: file_.read(1024 * hash_.block_size), b""):
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
    transfers_md_path = os.path.join(sip_path, "objects", "metadata", "transfers")
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
        path = os.path.join(sip_path, "objects", "metadata", filename)
        if os.path.isfile(path):
            paths.append(path)
    return paths


def create_directories(directories, basepath="", printing=False, printfn=print):
    """Create arbitrary directory structures given an iterable list of directory
    paths.
    """
    for directory in directories:
        dir_path = os.path.join(basepath, directory)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
            if printing:
                printfn("Creating directory", dir_path)


def create_structured_directory(
    basepath, manual_normalization=False, printing=False, printfn=print
):
    """Wrapper for create_directories for various structures required by
    Archivematica.
    """
    create_directories(
        REQUIRED_DIRECTORIES, basepath=basepath, printing=printing, printfn=printfn
    )
    if manual_normalization:
        create_directories(
            MANUAL_NORMALIZATION_DIRECTORIES,
            basepath=basepath,
            printing=printing,
            printfn=printfn,
        )


def get_dir_uuids(dir_paths, logger=None, printfn=print):
    """Return a generator of dict instances, each containing one of the
    directory paths in ``dir_paths`` and its newly minted UUID. Used by
    multiple client scripts.
    """
    for dir_path in dir_paths:
        dir_uuid = str(uuid4())
        msg = u"Assigning UUID {} to directory path {}".format(
            strToUnicode(dir_uuid), strToUnicode(dir_path)
        )
        printfn(msg)
        if logger:
            logger.info(msg)
        yield {"currentLocation": dir_path, "uuid": dir_uuid}


def format_subdir_path(dir_path, path_prefix_to_repl):
    """Add "/" to end of ``dir_path`` and replace actual root directory
    ``path_prefix_to_repl`` with a placeholder. Used when creating
    ``originallocation`` attributes for ``Directory`` models.
    """
    return os.path.join(dir_path, "").replace(
        path_prefix_to_repl, "%transferDirectory%", 1
    )


def walk_dir(dir_path):
    """Calculate directory size by recursively walking files.
    :param dir_path: absolute path to directory
    :return: size in bytes (int)
    """
    size = 0
    for dirpath, _, filenames in scandir.walk(dir_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            size += os.path.getsize(file_path)
    return size


def get_bag_size(bag, path):
    """Return size of BagIt Bag, using Payload-Oxum if present.

    Payload-Oxum, like other Bag Metadata elements, is optional per the BagIt
    specification: https://tools.ietf.org/html/rfc8493#section-2.2.2

    If the Bag does not have a Payload-Oxum, calculate size by recursively
    walking files.

    :param transfer_path: Bag object
    :param path: path to Bag directory
    :return: size in bytes (int)
    """
    oxum = bag.info.get("Payload-Oxum")
    if oxum is not None:
        return int(oxum.split(".")[0])
    return walk_dir(path)


def str2bool(val):
    """'True' is ``True``; aught else is ``False."""
    if val == "True":
        return True
    return False


NORMATIVE_STRUCTMAP_LABEL = "Normative Directory Structure"


def div_el_to_dir_paths(div_el, parent="", include=True):
    """Recursively extract the list of filesystem directory paths encoded in
    <mets:div> element ``div_el``.
    """
    paths = []
    path = parent
    dir_name = div_el.get("LABEL")
    if parent == "" and dir_name in ("metadata", "submissionDocumentation"):
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
    if not os.path.isfile(mets_file_path) or not os.path.isdir(objects_path):
        if logger:
            logger.info(
                u"Unable to construct empty directories, either because"
                " there is no METS file at {} or because there is no"
                " objects/ directory at {}".format(
                    strToUnicode(mets_file_path), strToUnicode(objects_path)
                )
            )
        return
    doc = etree.parse(mets_file_path, etree.XMLParser(remove_blank_text=True))
    logical_struct_map_el = doc.find(
        'mets:structMap[@TYPE="logical"][@LABEL="{}"]'.format(
            NORMATIVE_STRUCTMAP_LABEL
        ),
        NSMAP,
    )
    if logical_struct_map_el is None:
        if logger:
            logger.info(
                u"Unable to locate a logical structMap labelled {}."
                " Aborting attempt to reconstruct empty"
                " directories.".format(strToUnicode(NORMATIVE_STRUCTMAP_LABEL))
            )
        return
    root_div_el = logical_struct_map_el.find(
        'mets:div/mets:div[@LABEL="objects"]', NSMAP
    )
    if root_div_el is None:
        if logger:
            logger.info(
                u"Unable to locate a logical structMap labelled {}."
                " Aborting attempt to reconstruct empty"
                " directories.".format(strToUnicode(NORMATIVE_STRUCTMAP_LABEL))
            )
        return
    paths = div_el_to_dir_paths(root_div_el, include=False)
    if logger:
        logger.info("paths extracted from METS file:")
        logger.info(pprint.pformat(paths))
    for path in paths:
        path = os.path.join(objects_path, path)
        if not os.path.isdir(path):
            os.makedirs(path)


def find_transfer_path_from_ingest(transfer_path, shared_path):
    """Find path of a transfer arranged or coming straight from processing.

    In Ingest, access to the original transfers is needed in order to copy
    submission docs, metadata and logs. Transfers can be found under
    ``currentlyProcessing`` unless they come from SIP Arrangement, in which case
    they're found under the temporary shared directory.

    TODO: use ``Transfer.currentlocation`` or a model method?
    """
    transfer_uuid = transfer_path.rstrip("/")[-36:]

    path = transfer_path.replace("%sharedPath%", shared_path, 1)
    if os.path.isdir(path):
        return path

    path = os.path.join(shared_path, "tmp", "transfer-{}".format(transfer_uuid))
    if os.path.isdir(path):
        return path

    raise Exception("Transfer directory not physically found")


def find_aic_mets_filename(mets_root):
    """Find name of AIC METS file within AIP METS document.

    :param mets_root: AIP METS document root.

    :returns: AIC METS filename or None.
    """
    return xml_find_premis(
        mets_root, "mets:fileSec/mets:fileGrp[@USE='metadata']/mets:file/mets:FLocat"
    ).get("{" + NSMAP["xlink"] + "}href")


def find_aip_dirname(mets_root):
    """Find name of AIP directory within AIP METS document.

    :param mets_root: AIP METS document root.

    :returns: AIP dirname or None.
    """
    return xml_find_premis(mets_root, "mets:structMap/mets:div").get("LABEL")


def find_aips_in_aic(aic_root):
    """Find extent of AIPs in AIC within AIC METS document.

    :param aic_root" AIC METS document root.

    :returns: Count of AIPs in AIC or None.
    """
    extent = xml_find_premis(
        aic_root,
        "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore/dcterms:extent",
    )
    try:
        return re.search("\d+", extent.text).group()
    except AttributeError:
        return None


def package_name_from_path(current_path, remove_uuid_suffix=False):
    """Return name of package without file extensions from current path.

    This helper works for all package types (e.g. transfer, AIP, AIC).

    :param current_path: Current path to package.
    :param remove_uuid_suffix: Optional boolean to additionally remove
    UUID suffix.

    :returns: Package name minus any file extensions.
    """
    path = Path(current_path)
    name, chars_to_remove = path.name, 0
    if remove_uuid_suffix is True:
        chars_to_remove = PACKAGE_UUID_SUFFIX_LENGTH
    for suffix in reversed(path.suffixes):
        if suffix not in PACKAGE_EXTENSIONS:
            break
        chars_to_remove += len(suffix)
    # Check if we have characters to remove to avoid accidentally
    # returning an empty string with name[:-0].
    if not chars_to_remove:
        return name
    return name[:-chars_to_remove]


def relative_path_to_aip_mets_file(uuid, current_path):
    """Return relative path to AIP METS file.

    :param uuid: AIP UUID.
    :param current_path: Current path to AIP.

    :returns: Relative path to AIP METS file.
    """
    package_name_without_extensions = package_name_from_path(current_path)
    mets_name = "METS.{}.xml".format(uuid)
    mets_path = "{}/data/{}".format(package_name_without_extensions, mets_name)
    return mets_path
