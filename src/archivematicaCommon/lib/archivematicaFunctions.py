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
"""archivematicaFunctions provides various helper functions across the
different Archivematica modules.
"""

import base64
import collections
import errno
import glob
import hashlib
import locale
import os
import pprint
import re
from itertools import zip_longest
from pathlib import Path
from typing import Dict
from typing import Iterable
from uuid import uuid4

from amclient import AMClient
from django.apps import apps
from lxml import etree
from namespaces import NSMAP
from namespaces import xml_find_premis

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
            super().__setitem__(key, [])
        self[key].append(value)


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
    if isinstance(ret, str):
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace('"', '\\"')
        ret = ret.replace("`", r"\`")
        # ret = ret.replace("'", "\\'")
        # ret = ret.replace("$", "\\$")
    return ret


def escape(string):
    """Replace non-unicode characters with a replacement character. Use this
    primarily for arbitrary strings (e.g. filenames, paths) that might not
    be valid unicode to begin with.
    """
    if isinstance(string, bytes):
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


def find_mets_file(unit_path):
    """Return the location of the original METS in a Archivematica AIP transfer.

    :returns: Path to original METS file (str)

    :raises: METSDiscoveryError if no or multiple METS are found.
    """
    src = os.path.join(unit_path, "metadata")
    mets_paths = glob.glob(os.path.join(src, "METS.*.xml"))

    if len(mets_paths) == 1:
        return mets_paths[0]
    elif len(mets_paths) == 0:
        raise OSError(errno.EEXIST, f"No METS file found in {src}")
    else:
        raise OSError(errno.EEXIST, f"Multiple METS files found in {src}: {mets_paths}")


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
        msg = f"Assigning UUID {dir_uuid} to directory path {dir_path}"
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
    for dirpath, _, filenames in os.walk(dir_path):
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
                "Unable to construct empty directories, either because"
                f" there is no METS file at {mets_file_path} or because there is no"
                f" objects/ directory at {objects_path}"
            )
        return
    doc = etree.parse(mets_file_path, etree.XMLParser(remove_blank_text=True))
    logical_struct_map_el = doc.find(
        f'mets:structMap[@TYPE="logical"][@LABEL="{NORMATIVE_STRUCTMAP_LABEL}"]',
        NSMAP,
    )
    if logical_struct_map_el is None:
        if logger:
            logger.info(
                f"Unable to locate a logical structMap labelled {NORMATIVE_STRUCTMAP_LABEL}."
                " Aborting attempt to reconstruct empty"
                " directories."
            )
        return
    root_div_el = logical_struct_map_el.find(
        'mets:div/mets:div[@LABEL="objects"]', NSMAP
    )
    if root_div_el is None:
        if logger:
            logger.info(
                f"Unable to locate a logical structMap labelled {NORMATIVE_STRUCTMAP_LABEL}."
                " Aborting attempt to reconstruct empty"
                " directories."
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

    path = os.path.join(shared_path, "tmp", f"transfer-{transfer_uuid}")
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
        return re.search(r"\d+", extent.text).group()
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
    mets_name = f"METS.{uuid}.xml"
    mets_path = f"{package_name_without_extensions}/data/{mets_name}"
    return mets_path


def chunk_iterable(iterable, chunk_size=10, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.
    >>> list(chunk_iterable('ABCDEFG', 3, 'x'))
    [('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'x', 'x')]
    """
    args = [iter(iterable)] * chunk_size
    return zip_longest(*args, fillvalue=fillvalue)


def get_oidc_secondary_providers(
    oidc_secondary_provider_names: Iterable[str],
) -> Dict[str, Dict[str, str]]:
    """Build secondary OIDC provider details dict. Takes a list of secondary
    OIDC providers and gathers details about these providers from env vars.
    Output dict contains details for each OIDC connection which can then be
    referenced by name.
    """

    providers = {}

    for provider_name in oidc_secondary_provider_names:
        provider_name = provider_name.strip().upper()
        client_id = os.environ.get(f"OIDC_RP_CLIENT_ID_{provider_name}")
        client_secret = os.environ.get(f"OIDC_RP_CLIENT_SECRET_{provider_name}")
        authorization_endpoint = os.environ.get(
            f"OIDC_OP_AUTHORIZATION_ENDPOINT_{provider_name}", ""
        )
        token_endpoint = os.environ.get(f"OIDC_OP_TOKEN_ENDPOINT_{provider_name}", "")
        user_endpoint = os.environ.get(f"OIDC_OP_USER_ENDPOINT_{provider_name}", "")
        jwks_endpoint = os.environ.get(f"OIDC_OP_JWKS_ENDPOINT_{provider_name}", "")
        logout_endpoint = os.environ.get(f"OIDC_OP_LOGOUT_ENDPOINT_{provider_name}", "")

        if client_id and client_secret:
            providers[provider_name] = {
                "OIDC_RP_CLIENT_ID": client_id,
                "OIDC_RP_CLIENT_SECRET": client_secret,
                "OIDC_OP_AUTHORIZATION_ENDPOINT": authorization_endpoint,
                "OIDC_OP_TOKEN_ENDPOINT": token_endpoint,
                "OIDC_OP_USER_ENDPOINT": user_endpoint,
                "OIDC_OP_JWKS_ENDPOINT": jwks_endpoint,
                "OIDC_OP_LOGOUT_ENDPOINT": logout_endpoint,
            }

    return providers
