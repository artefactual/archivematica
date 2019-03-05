# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @author Mike Cantelon <mike@artefactual.com>

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import calendar
import datetime
import json
import logging
import os
import re
import sys
import time
from xml.etree import ElementTree

from django.db.models import Q
from django.utils.six.moves import xrange
from main.models import File, Transfer

# archivematicaCommon
from archivematicaFunctions import get_dashboard_uuid
import namespaces as ns
import version

from externals import xmltodict

from elasticsearch import Elasticsearch, ImproperlyConfigured


logger = logging.getLogger("archivematica.common")


class ElasticsearchError(Exception):
    """ Not operational errors. """

    pass


class EmptySearchResultError(ElasticsearchError):
    pass


class TooManyResultsError(ElasticsearchError):
    pass


_es_hosts = None
_es_client = None
DEFAULT_TIMEOUT = 10
# Known indexes. This indexes may be enabled or not based on the SEARCH_ENABLED
# setting. To add a new index, make sure it's related to the setting values in
# the setup functions below, add its name to the following array and create a
# function declaring the index settings and mapping. For example, for an index
# called `tests` the function must be called `_get_tests_index_body`. See the
# functions related to the current known indexes for examples.
INDEXES = ["aips", "aipfiles", "transfers", "transferfiles"]
# A doc type is still required in ES 6.x but it's limited to one per index.
# It will be removed in ES 7.x, so we'll use the same for all indexes.
DOC_TYPE = "_doc"
# Maximun ES result window. Use the scroll API for a better way to get all
# results or change `index.max_result_window` on each index settings.
MAX_QUERY_SIZE = 10000


def setup(hosts, timeout=DEFAULT_TIMEOUT, enabled=["aips", "transfers"]):
    """Initialize and share the Elasticsearch client.

    Share it as the attribute _es_client in the current module. An additional
    attribute _es_hosts is defined containing the Elasticsearch hosts (expected
    types are: string, list or tuple). Also, the existence of the enabled
    indexes is checked to be able to create the required indexes on the fly if
    they don't exist.
    """
    global _es_hosts
    global _es_client

    _es_hosts = hosts
    _es_client = Elasticsearch(
        **{"hosts": _es_hosts, "timeout": timeout, "dead_timeout": 2}
    )

    # TODO: Do we really need to be able to create the indexes
    # on the fly? Could we force to run the rebuild commands and
    # avoid doing this on each setup?
    indexes = []
    if "aips" in enabled:
        indexes.extend(["aips", "aipfiles"])
    if "transfers" in enabled:
        indexes.extend(["transfers", "transferfiles"])
    if len(indexes) > 0:
        create_indexes_if_needed(_es_client, indexes)
    else:
        logger.warning(
            "Setting up the Elasticsearch client " "without enabled indexes."
        )


def setup_reading_from_conf(settings):
    setup(
        settings.ELASTICSEARCH_SERVER,
        settings.ELASTICSEARCH_TIMEOUT,
        settings.SEARCH_ENABLED,
    )


def get_client():
    """Obtain the current Elasticsearch client.

    If undefined, an exception will be raised. This function also checks the
    integrity of the indexes expected by this application and populate them
    when they cannot be found.
    """
    if not _es_client:
        raise ImproperlyConfigured(
            "The Elasticsearch client has not been set up yet. Please call setup() first."
        )
    return _es_client


def _wait_for_cluster_yellow_status(client, wait_between_tries=10, max_tries=10):
    health = {}
    health["status"] = None
    tries = 0

    # Wait for either yellow or green status
    while (
        health["status"] != "yellow"
        and health["status"] != "green"
        and tries < max_tries
    ):
        tries = tries + 1

        try:
            health = client.cluster.health()
        except:
            print("ERROR: failed health check.")
            health["status"] = None

        # Sleep if cluster not healthy
        if health["status"] != "yellow" and health["status"] != "green":
            print("Cluster not in yellow or green state... waiting to retry.")
            time.sleep(wait_between_tries)


# --------------
# CREATE INDEXES
# --------------


def create_indexes_if_needed(client, indexes):
    """Checks if the indexes passed exist in the client.

    Otherwise, creates the missing ones with their settings and mappings.
    """
    if client.indices.exists(index=",".join(indexes)):
        logger.info("All indexes already created.")
        return
    for index in indexes:
        if index not in INDEXES:
            logger.warning('Index "%s" not recognized. Skipping.', index)
            continue
        # Call get index body functions below for each index
        body = getattr(sys.modules[__name__], "_get_%s_index_body" % index)()
        logger.info('Creating "%s" index ...', index)
        client.indices.create(index, body=body, ignore=400)
        logger.info("Index created.")


def _get_aips_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "date_detection": False,
                "properties": {
                    "name": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "size": {"type": "double"},
                    "uuid": {"type": "keyword"},
                    "mets": _load_mets_mapping("aips"),
                },
            }
        },
    }


def _get_aipfiles_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "date_detection": False,
                "properties": {
                    "sipName": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "AIPUUID": {"type": "keyword"},
                    "FILEUUID": {"type": "keyword"},
                    "isPartOf": {"type": "keyword"},
                    "AICID": {"type": "keyword"},
                    "indexedAt": {"type": "double"},
                    "filePath": {"type": "text", "analyzer": "file_path_and_name"},
                    "fileExtension": {"type": "text"},
                    "origin": {"type": "text"},
                    "identifiers": {"type": "keyword"},
                    "METS": _load_mets_mapping("aipfiles"),
                },
            }
        },
    }


def _get_transfers_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "properties": {
                    "name": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "status": {"type": "text"},
                    "ingest_date": {"type": "date", "format": "dateOptionalTime"},
                    "file_count": {"type": "integer"},
                    "uuid": {"type": "keyword"},
                    "pending_deletion": {"type": "boolean"},
                }
            }
        },
    }


def _get_transferfiles_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "properties": {
                    "filename": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "relative_path": {"type": "text", "analyzer": "file_path_and_name"},
                    "fileuuid": {"type": "keyword"},
                    "sipuuid": {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "origin": {"type": "keyword"},
                    "ingestdate": {"type": "date", "format": "dateOptionalTime"},
                    # METS.xml files in transfers sent to backlog will have ''
                    # as their modification_date value. This can cause a
                    # failure in certain cases, see:
                    # https://github.com/artefactual/archivematica/issues/719.
                    # For this reason, we specify the type and format here and
                    # ignore malformed values like ''.
                    "modification_date": {
                        "type": "date",
                        "format": "dateOptionalTime",
                        "ignore_malformed": True,
                    },
                    "created": {"type": "double"},
                    "size": {"type": "double"},
                    "tags": {"type": "keyword"},
                    "file_extension": {"type": "keyword"},
                    "bulk_extractor_reports": {"type": "keyword"},
                    "format": {
                        "type": "nested",
                        "properties": {
                            "puid": {"type": "keyword"},
                            "format": {"type": "text"},
                            "group": {"type": "text"},
                        },
                    },
                }
            }
        },
    }


def _load_mets_mapping(index):
    """Load external METS mappings.

    These were generated from an AIP which had all the metadata fields filled
    out and should represent a pretty complete structure.
    We don't want to leave this up to dynamic mapping, since automatic type
    detection may result in some fields being detected as date fields, and
    subsequently causing problems.
    """
    json_file = "%s_mets_mapping.json" % index
    path = os.path.join(__file__, "..", "elasticsearch", json_file)
    with open(os.path.normpath(path)) as f:
        return json.load(f)


def _get_index_settings():
    """Returns a dictionary with the settings used in all indexes."""
    return {
        "analysis": {
            "analyzer": {
                # Use the char_group tokenizer to split paths and filenames,
                # including file extensions, which avoids the overhead of the
                # pattern tokenizer.
                "file_path_and_name": {
                    "tokenizer": "char_tokenizer",
                    "filter": ["lowercase"],
                }
            },
            "tokenizer": {
                "char_tokenizer": {
                    "type": "char_group",
                    "tokenize_on_chars": ["-", "_", ".", "/", "\\"],
                }
            },
        }
    }


# ---------------
# INDEX RESOURCES
# ---------------


def index_aip_and_files(
    client,
    uuid,
    path,
    mets_path,
    name,
    size=None,
    aips_in_aic=None,
    identifiers=[],
    encrypted=False,
    printfn=print,
):
    """Index AIP and AIP files with UUID `uuid` at path `path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the AIP we're indexing.
    :param path: path on disk where the AIP is located.
    :param path: path on disk where the AIP's METS file is located.
    :param name: AIP name.
    :param size: optional AIP size.
    :param aips_in_aic: optional number of AIPs stored in AIC.
    :param identifiers: optional additional identifiers (MODS, Islandora, etc.).
    :param identifiers: optional AIP encrypted boolean (defaults to `False`).
    :param printfn: optional print funtion.
    :return: 0 is succeded, 1 otherwise.
    """
    # Stop if AIP or METS file don't not exist
    error_message = None
    if not os.path.exists(path):
        error_message = "AIP does not exist at: " + path
    if not os.path.exists(mets_path):
        error_message = "METS file does not exist at: " + mets_path
    if error_message:
        logger.error(error_message)
        printfn(error_message, file=sys.stderr)
        return 1

    printfn("AIP UUID: " + uuid)
    printfn("Indexing AIP ...")

    tree = ElementTree.parse(mets_path)

    # TODO: Add a conditional to toggle this
    _remove_tool_output_from_mets(tree)

    root = tree.getroot()
    # Extract AIC identifier, other specially-indexed information
    aic_identifier = None
    is_part_of = None
    dublincore = root.find(
        "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore", namespaces=ns.NSMAP
    )
    if dublincore is not None:
        aip_type = dublincore.findtext(
            "dc:type", namespaces=ns.NSMAP
        ) or dublincore.findtext("dcterms:type", namespaces=ns.NSMAP)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext(
                "dc:identifier", namespaces=ns.NSMAP
            ) or dublincore.findtext("dcterms:identifier", namespaces=ns.NSMAP)
        is_part_of = dublincore.findtext("dcterms:isPartOf", namespaces=ns.NSMAP)

    # Convert METS XML to dict
    xml = ElementTree.tostring(root)
    mets_data = _rename_dict_keys_with_child_dicts(
        _normalize_dict_values(xmltodict.parse(xml))
    )

    # Pull the create time from the METS header
    mets_hdr = root.find("mets:metsHdr", namespaces=ns.NSMAP)
    mets_created_attr = mets_hdr.get("CREATEDATE")

    created = time.time()

    if mets_created_attr:
        try:
            created = calendar.timegm(
                time.strptime(mets_created_attr, "%Y-%m-%dT%H:%M:%S")
            )
        except ValueError:
            printfn("Failed to parse METS CREATEDATE: %s" % (mets_created_attr))

    aip_data = {
        "uuid": uuid,
        "name": name,
        "filePath": path,
        "size": (size or os.path.getsize(path)) / 1024 / 1024,
        "mets": mets_data,
        "origin": get_dashboard_uuid(),
        "created": created,
        "AICID": aic_identifier,
        "isPartOf": is_part_of,
        "countAIPsinAIC": aips_in_aic,
        "identifiers": identifiers,
        "transferMetadata": _extract_transfer_metadata(root),
        "encrypted": encrypted,
    }
    _wait_for_cluster_yellow_status(client)
    _try_to_index(client, aip_data, "aips", printfn=printfn)
    printfn("Done.")

    printfn("Indexing AIP files ...")
    files_indexed = _index_aip_files(
        client=client,
        uuid=uuid,
        mets_path=mets_path,
        name=name,
        identifiers=identifiers,
        printfn=printfn,
    )

    printfn("Files indexed: " + str(files_indexed))
    return 0


def _index_aip_files(client, uuid, mets_path, name, identifiers=[], printfn=print):
    """Index AIP files from AIP with UUID `uuid` and METS at path `mets_path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the AIP we're indexing.
    :param mets_path: path on disk where the AIP's METS file is located.
    :param name: AIP name.
    :param identifiers: optional additional identifiers (MODS, Islandora, etc.).
    :param printfn: optional print funtion.
    :return: number of files indexed.
    """
    # Parse XML
    tree = ElementTree.parse(mets_path)
    root = tree.getroot()

    # TODO: Add a conditional to toggle this
    _remove_tool_output_from_mets(tree)

    # Extract isPartOf (for AIPs) or identifier (for AICs) from DublinCore
    dublincore = root.find(
        "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore", namespaces=ns.NSMAP
    )
    aic_identifier = None
    is_part_of = None
    if dublincore is not None:
        aip_type = dublincore.findtext(
            "dc:type", namespaces=ns.NSMAP
        ) or dublincore.findtext("dcterms:type", namespaces=ns.NSMAP)
        if aip_type == "Archival Information Collection":
            aic_identifier = dublincore.findtext(
                "dc:identifier", namespaces=ns.NSMAP
            ) or dublincore.findtext("dcterms:identifier", namespaces=ns.NSMAP)
        elif aip_type == "Archival Information Package":
            is_part_of = dublincore.findtext("dcterms:isPartOf", namespaces=ns.NSMAP)

    # Establish structure to be indexed for each file item
    fileData = {
        "archivematicaVersion": version.get_version(),
        "AIPUUID": uuid,
        "sipName": name,
        "FILEUUID": "",
        "indexedAt": time.time(),
        "filePath": "",
        "fileExtension": "",
        "isPartOf": is_part_of,
        "AICID": aic_identifier,
        "METS": {"dmdSec": {}, "amdSec": {}},
        "origin": get_dashboard_uuid(),
        "identifiers": identifiers,
        "transferMetadata": _extract_transfer_metadata(root),
    }

    # Index all files in a fileGrup with USE='original' or USE='metadata'
    original_files = root.findall(
        "mets:fileSec/mets:fileGrp[@USE='original']/mets:file", namespaces=ns.NSMAP
    )
    metadata_files = root.findall(
        "mets:fileSec/mets:fileGrp[@USE='metadata']/mets:file", namespaces=ns.NSMAP
    )
    files = original_files + metadata_files

    # Index AIC METS file if it exists
    for file_ in files:
        indexData = fileData.copy()  # Deep copy of dict, not of dict contents

        # Get file UUID.  If and ADMID exists, look in the amdSec for the UUID,
        # otherwise parse it out of the file ID.
        # 'Original' files have ADMIDs, 'Metadata' files don't
        admID = file_.attrib.get("ADMID", None)
        if admID is None:
            # Parse UUID from file ID
            fileUUID = None
            uuix_regex = r"\w{8}-?\w{4}-?\w{4}-?\w{4}-?\w{12}"
            uuids = re.findall(uuix_regex, file_.attrib["ID"])
            # Multiple UUIDs may be returned - if they are all identical, use that
            # UUID, otherwise use None.
            # To determine all UUIDs are identical, use the size of the set
            if len(set(uuids)) == 1:
                fileUUID = uuids[0]
        else:
            amdSecInfo = root.find(
                "mets:amdSec[@ID='{}']".format(admID), namespaces=ns.NSMAP
            )
            fileUUID = amdSecInfo.findtext(
                "mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectIdentifier/premis:objectIdentifierValue",
                namespaces=ns.NSMAP,
            )

            # Index amdSec information
            xml = ElementTree.tostring(amdSecInfo)
            indexData["METS"]["amdSec"] = _rename_dict_keys_with_child_dicts(
                _normalize_dict_values(xmltodict.parse(xml))
            )

        # Get the parent division for the file pointer
        # by searching the physical structural map section (structMap)
        file_id = file_.attrib.get("ID", None)
        file_pointer_division = root.find(
            "mets:structMap[@TYPE='physical']//mets:fptr[@FILEID='{}']/..".format(
                file_id
            ),
            namespaces=ns.NSMAP,
        )
        if file_pointer_division is not None:
            # If the parent division has a DMDID attribute then index
            # its data from the descriptive metadata section (dmdSec)
            dmd_section_id = file_pointer_division.attrib.get("DMDID", None)
            if dmd_section_id is not None:
                dmd_section_info = root.find(
                    "mets:dmdSec[@ID='{}']/mets:mdWrap/mets:xmlData".format(
                        dmd_section_id
                    ),
                    namespaces=ns.NSMAP,
                )
                xml = ElementTree.tostring(dmd_section_info)
                data = _rename_dict_keys_with_child_dicts(
                    _normalize_dict_values(xmltodict.parse(xml))
                )
                indexData["METS"]["dmdSec"] = data

        indexData["FILEUUID"] = fileUUID

        # Get file path from FLocat and extension
        filePath = file_.find("mets:FLocat", namespaces=ns.NSMAP).attrib[
            "{http://www.w3.org/1999/xlink}href"
        ]
        indexData["filePath"] = filePath
        _, fileExtension = os.path.splitext(filePath)
        if fileExtension:
            indexData["fileExtension"] = fileExtension[1:].lower()

        # Index data
        _wait_for_cluster_yellow_status(client)
        _try_to_index(client, indexData, "aipfiles", printfn=printfn)

        # Reset fileData['METS']['amdSec'] and fileData['METS']['dmdSec'],
        # since they are updated in the loop above.
        # See http://stackoverflow.com/a/3975388 for explanation
        fileData["METS"]["amdSec"] = {}
        fileData["METS"]["dmdSec"] = {}

    return len(files)


def index_transfer_and_files(client, uuid, path, printfn=print):
    """Indexes Transfer and Transfer files with UUID `uuid` at path `path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the transfer we're indexing.
    :param path: path on disk, including the transfer directory and a
                 trailing / but not including objects/.
    :param printfn: optional print funtion.
    :return: 0 is succeded, 1 otherwise.
    """
    # Stop if Transfer does not exist
    if not os.path.exists(path):
        error_message = "Transfer does not exist at: " + path
        logger.error(error_message)
        printfn(error_message, file=sys.stderr)
        return 1

    # Default status of a transfer file document in the index.
    status = "backlog"

    printfn("Transfer UUID: " + uuid)
    printfn("Indexing Transfer files ...")
    files_indexed = _index_transfer_files(
        client, uuid, path, status=status, printfn=printfn
    )

    printfn("Files indexed: " + str(files_indexed))
    printfn("Indexing Transfer ...")

    try:
        transfer = Transfer.objects.get(uuid=uuid)
        transfer_name = transfer.currentlocation.split("/")[-2]
    except Transfer.DoesNotExist:
        transfer_name = ""

    transfer_data = {
        "name": transfer_name,
        "status": status,
        "ingest_date": str(datetime.datetime.today())[0:10],
        "file_count": files_indexed,
        "uuid": uuid,
        "pending_deletion": False,
    }

    _wait_for_cluster_yellow_status(client)
    _try_to_index(client, transfer_data, "transfers", printfn=printfn)
    printfn("Done.")

    return 0


def _index_transfer_files(client, uuid, path, status="", printfn=print):
    """Indexes files in the Transfer with UUID `uuid` at path `path`.

    :param client: ElasticSearch client.
    :param uuid: UUID of the Transfer in the DB.
    :param path: path on disk, including the transfer directory and a
                 trailing / but not including objects/.
    :param status: optional Transfer status.
    :param printfn: optional print funtion.
    :return: number of files indexed.
    """
    files_indexed = 0
    ingest_date = str(datetime.datetime.today())[0:10]

    # Some files should not be indexed.
    # This should match the basename of the file.
    ignore_files = ["processingMCP.xml"]

    # Get accessionId and name from Transfers table using UUID
    try:
        transfer = Transfer.objects.get(uuid=uuid)
        accession_id = transfer.accessionid
        transfer_name = transfer.currentlocation.split("/")[-2]
    except Transfer.DoesNotExist:
        accession_id = transfer_name = ""

    # Get dashboard UUID
    dashboard_uuid = get_dashboard_uuid()

    for filepath in _list_files_in_dir(path):
        if os.path.isfile(filepath):
            # We need to account for the possibility of dealing with a BagIt
            # transfer package - the new default in Archivematica.
            # The BagIt is created when the package is sent to backlog hence
            # the locations in the database do not reflect the BagIt paths.
            # Strip the "data/" part when looking up the file entry.
            currentlocation = "%transferDirectory%" + os.path.relpath(
                filepath, path
            ).lstrip("data/")
            try:
                f = File.objects.get(currentlocation=currentlocation, transfer_id=uuid)
                file_uuid = f.uuid
                formats = _get_file_formats(f)
                bulk_extractor_reports = _list_bulk_extractor_reports(path, file_uuid)
                if f.modificationtime is not None:
                    modification_date = f.modificationtime.strftime("%Y-%m-%d")
            except File.DoesNotExist:
                file_uuid, modification_date = "", ""
                formats = []
                bulk_extractor_reports = []

            # Get file path info
            relative_path = filepath.replace(path, transfer_name + "/")
            file_extension = os.path.splitext(filepath)[1][1:].lower()
            filename = os.path.basename(filepath)
            # Size in megabytes
            size = os.path.getsize(filepath) / (1024 * 1024)
            create_time = os.stat(filepath).st_ctime

            if filename not in ignore_files:
                printfn("Indexing {} (UUID: {})".format(relative_path, file_uuid))

                # TODO: Index Backlog Location UUID?
                indexData = {
                    "filename": filename,
                    "relative_path": relative_path,
                    "fileuuid": file_uuid,
                    "sipuuid": uuid,
                    "accessionid": accession_id,
                    "status": status,
                    "origin": dashboard_uuid,
                    "ingestdate": ingest_date,
                    "created": create_time,
                    "modification_date": modification_date,
                    "size": size,
                    "tags": [],
                    "file_extension": file_extension,
                    "bulk_extractor_reports": bulk_extractor_reports,
                    "format": formats,
                }

                _wait_for_cluster_yellow_status(client)
                _try_to_index(client, indexData, "transferfiles", printfn=printfn)

                files_indexed = files_indexed + 1
            else:
                printfn("Skipping indexing {}".format(relative_path))

    return files_indexed


def _try_to_index(
    client, data, index, wait_between_tries=10, max_tries=10, printfn=print
):
    exception = None
    if max_tries < 1:
        raise ValueError("max_tries must be 1 or greater")
    for _ in xrange(0, max_tries):
        try:
            client.index(body=data, index=index, doc_type=DOC_TYPE)
            return
        except Exception as e:
            exception = e
            printfn("ERROR: error trying to index.")
            printfn(e)
            time.sleep(wait_between_tries)

    # If indexing did not succeed after max_tries is already complete,
    # reraise the Elasticsearch exception to aid in debugging.
    if exception:
        raise exception


# ----------------
# INDEXING HELPERS
# ----------------


def _remove_tool_output_from_mets(doc):
    """Remove tool output from a METS ElementTree.

    Given an ElementTree object, removes all objectsCharacteristicsExtensions
    elements. This modifies the existing document in-place; it does not return
    a new document. This helps index METS files, which might otherwise get too
    large to be usable.
    """
    root = doc.getroot()

    # Remove tool output nodes
    toolNodes = root.findall(
        "mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension",
        namespaces=ns.NSMAP,
    )

    for parent in toolNodes:
        parent.clear()

    print("Removed FITS output from METS.")


def _extract_transfer_metadata(doc):
    return [
        xmltodict.parse(ElementTree.tostring(el))["transfer_metadata"]
        for el in doc.findall(
            "mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/transfer_metadata",
            namespaces=ns.NSMAP,
        )
    ]


def _rename_dict_keys_with_child_dicts(data):
    """Rename dictionary keys.

    To avoid Elasticsearch schema collisions, if a dict value is itself a
    dict then rename the dict key to differentiate it from similar instances
    where the same key has a different value type.
    """
    new = {}
    for key in data:
        if isinstance(data[key], dict):
            new[key + "_data"] = _rename_dict_keys_with_child_dicts(data[key])
        elif isinstance(data[key], list):
            # Elasticsearch's lists are typed; a list of strings and
            # a list of objects are not the same type. Check the type
            # of the first object in the list and use that as the tag,
            # rather than just tagging this "_list"
            type_of_list = type(data[key][0]).__name__
            value = _rename_list_elements_if_they_are_dicts(data[key])
            new[key + "_" + type_of_list + "_list"] = value
        else:
            new[key] = data[key]
    return new


def _rename_list_elements_if_they_are_dicts(data):
    for index, value in enumerate(data):
        if isinstance(value, list):
            data[index] = _rename_list_elements_if_they_are_dicts(value)
        elif isinstance(value, dict):
            data[index] = _rename_dict_keys_with_child_dicts(value)
    return data


def _normalize_dict_values(data):
    """Normalize dictionary values.

    Because an XML document node may include one or more children, conversion
    to a dict can result in the converted child being one of two types.
    this causes problems in an Elasticsearch index as it expects consistant
    types to be indexed.
    The below function recurses a dict and if a dict's value is another dict,
    it encases it in a list.
    """
    for key in data:
        if isinstance(data[key], dict):
            data[key] = [_normalize_dict_values(data[key])]
        elif isinstance(data[key], list):
            data[key] = _normalize_list_dict_elements(data[key])
    return data


def _normalize_list_dict_elements(data):
    for index, value in enumerate(data):
        if isinstance(value, list):
            data[index] = _normalize_list_dict_elements(value)
        elif isinstance(value, dict):
            data[index] = _normalize_dict_values(value)
    return data


def _get_file_formats(f):
    formats = []
    fields = [
        "format_version__pronom_id",
        "format_version__description",
        "format_version__format__group__description",
    ]
    for puid, format, group in f.fileformatversion_set.all().values_list(*fields):
        formats.append({"puid": puid, "format": format, "group": group})

    return formats


def _list_bulk_extractor_reports(transfer_path, file_uuid):
    reports = []
    log_path = os.path.join(transfer_path, "logs", "bulk-" + file_uuid)

    if not os.path.isdir(log_path):
        return reports
    for report in ["telephone", "ccn", "ccn_track2", "pii"]:
        path = os.path.join(log_path, report + ".txt")
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            reports.append(report)

    return reports


def _list_files_in_dir(path, filepaths=[]):
    # Define entries
    for file in os.listdir(path):
        child_path = os.path.join(path, file)
        filepaths.append(child_path)

        # If entry is a directory, recurse
        if os.path.isdir(child_path) and os.access(child_path, os.R_OK):
            _list_files_in_dir(child_path, filepaths)

    # Return fully traversed data
    return filepaths


# -------
# QUERIES
# -------


def search_all_results(client, body, index):
    """Performs client.search with the size set to MAX_QUERY_SIZE.

    By default search_raw returns only 10 results. Since we usually want all
    results, this is a wrapper that fetches MAX_QUERY_SIZE results and logs a
    warning if more results were available.
    """
    if isinstance(index, list):
        index = ",".join(index)

    results = client.search(body=body, index=index, size=MAX_QUERY_SIZE)

    if results["hits"]["total"] > MAX_QUERY_SIZE:
        logger.warning(
            "Number of items in backlog (%s) exceeds maximum amount " "fetched (%s)",
            results["hits"]["total"],
            MAX_QUERY_SIZE,
        )
    return results


def get_aip_data(client, uuid, fields=None):
    search_params = {"body": {"query": {"term": {"uuid": uuid}}}, "index": "aips"}

    if fields:
        search_params["_source"] = fields

    aips = client.search(**search_params)

    return aips["hits"]["hits"][0]


def _document_ids_from_field_query(client, index, field, value):
    document_ids = []

    # Escape /'s with \\
    searchvalue = value.replace("/", "\\/")
    query = {"query": {"term": {field: searchvalue}}}
    documents = search_all_results(client, body=query, index=index)

    if len(documents["hits"]["hits"]) > 0:
        document_ids = [d["_id"] for d in documents["hits"]["hits"]]

    return document_ids


def _document_id_from_field_query(client, index, field, value):
    document_id = None
    ids = _document_ids_from_field_query(client, index, field, value)
    if len(ids) == 1:
        document_id = ids[0]
    return document_id


def get_file_tags(client, uuid):
    """Gets the tags of a given file by its UUID.

    Retrieve the complete set of tags for the file with the fileuuid `uuid`.
    Returns a list of zero or more strings.

    :param Elasticsearch client: Elasticsearch client
    :param str uuid: A file UUID.
    """
    query = {"query": {"term": {"fileuuid": uuid}}}

    results = client.search(body=query, index="transferfiles", _source="tags")

    count = results["hits"]["total"]
    if count == 0:
        raise EmptySearchResultError(
            "No matches found for file with UUID {}".format(uuid)
        )
    if count > 1:
        raise TooManyResultsError(
            "{} matches found for file with UUID {}; unable to fetch a single result".format(
                count, uuid
            )
        )

    result = results["hits"]["hits"][0]
    # File has no tags
    if "_source" not in result:
        return []
    return result["_source"]["tags"]


def set_file_tags(client, uuid, tags):
    """Updates the file(s) with the fileuuid `uuid` to the provided value(s).

    :param Elasticsearch client: Elasticsearch client
    :param str uuid: A file UUID.
    :param list tags: A list of zero or more tags.
        Passing an empty list clears the file's tags.
    """
    document_ids = _document_ids_from_field_query(
        client, "transferfiles", "fileuuid", uuid
    )

    count = len(document_ids)
    if count == 0:
        raise EmptySearchResultError(
            "No matches found for file with UUID {}".format(uuid)
        )
    if count > 1:
        raise TooManyResultsError(
            "{} matches found for file with UUID {}; unable to fetch a single result".format(
                count, uuid
            )
        )

    body = {"doc": {"tags": tags}}
    client.update(
        body=body, index="transferfiles", doc_type=DOC_TYPE, id=document_ids[0]
    )
    return True


def get_transfer_file_info(client, field, value):
    """
    Get transferfile information from ElasticSearch with query field = value.
    """
    logger.debug("get_transfer_file_info: field: %s, value: %s", field, value)
    results = {}
    query = {"query": {"term": {field: value}}}
    documents = search_all_results(client, body=query, index="transferfiles")
    result_count = len(documents["hits"]["hits"])
    if result_count == 1:
        results = documents["hits"]["hits"][0]["_source"]
    elif result_count > 1:
        # Elasticsearch was sometimes ranking results for a different filename above
        # the actual file being queried for; in that case only consider results
        # where the value is an actual precise match.
        filtered_results = [
            results
            for results in documents["hits"]["hits"]
            if results["_source"][field] == value
        ]

        result_count = len(filtered_results)
        if result_count == 1:
            results = filtered_results[0]["_source"]
        if result_count > 1:
            results = filtered_results[0]["_source"]
            logger.warning(
                "get_transfer_file_info returned %s results for query %s: %s (using first result)",
                result_count,
                field,
                value,
            )
        elif result_count < 1:
            logger.error(
                "get_transfer_file_info returned no exact results for query %s: %s",
                field,
                value,
            )
            raise ElasticsearchError("get_transfer_file_info returned no exact results")

    logger.debug("get_transfer_file_info: results: %s", results)
    return results


# -------
# DELETES
# -------


def remove_backlog_transfer(client, uuid):
    _delete_matching_documents(client, "transfers", "uuid", uuid)


def remove_backlog_transfer_files(client, uuid):
    _remove_transfer_files(client, uuid, "transfer")


def remove_sip_transfer_files(client, uuid):
    _remove_transfer_files(client, uuid, "sip")


def _remove_transfer_files(client, uuid, unit_type=None):
    if unit_type == "transfer":
        transfers = {uuid}
    else:
        condition = Q(transfer_id=uuid) | Q(sip_id=uuid)
        transfers = {
            f[0] for f in File.objects.filter(condition).values_list("transfer_id")
        }

    if len(transfers) > 0:
        for transfer in transfers:
            files = _document_ids_from_field_query(
                client, "transferfiles", "sipuuid", transfer
            )
            if len(files) > 0:
                for file_id in files:
                    client.delete(index="transferfiles", doc_type=DOC_TYPE, id=file_id)
    else:
        if not unit_type:
            unit_type = "transfer or SIP"
        logger.warning("No transfers found for %s %s", unit_type, uuid)


def delete_aip(client, uuid):
    _delete_matching_documents(client, "aips", "uuid", uuid)


def delete_aip_files(client, uuid):
    _delete_matching_documents(client, "aipfiles", "AIPUUID", uuid)


def _delete_matching_documents(client, index, field, value):
    """Deletes all documents in index where field = value

    :param Elasticsearch client: Elasticsearch client
    :param str index: Name of the index. E.g. 'aips'
    :param str field: Field to query when deleting. E.g. 'uuid'
    :param str value: Value of the field to query when deleting. E.g. 'cd0bb626-cf27-4ca3-8a77-f14496b66f04'
    """
    query = {"query": {"term": {field: value}}}
    logger.info("Deleting with query %s", query)
    results = client.delete_by_query(index=index, body=query)
    logger.info("Deleted by query %s", results)


# -------
# UPDATES
# -------


def _update_field(client, index, uuid, field, value):
    document_id = _document_id_from_field_query(client, index, "uuid", uuid)

    if document_id is None:
        logger.error(
            "Unable to find document with UUID {} in index {}".format(uuid, index)
        )
        return

    client.update(
        body={"doc": {field: value}}, index=index, doc_type=DOC_TYPE, id=document_id
    )


def mark_aip_deletion_requested(client, uuid):
    _update_field(client, "aips", uuid, "status", "DEL_REQ")


def mark_aip_stored(client, uuid):
    _update_field(client, "aips", uuid, "status", "UPLOADED")


def mark_backlog_deletion_requested(client, uuid):
    _update_field(client, "transfers", uuid, "pending_deletion", True)


# ---------------
# RESULTS HELPERS
# ---------------


def augment_raw_search_results(raw_results):
    """Normalize search results response.

    This function takes JSON returned by an ES query and returns the source
    document for each result.

    :param raw_results: the raw JSON result from an elastic search query
    :return: JSON result simplified, with document_id set
    """
    modifiedResults = []

    for item in raw_results["hits"]["hits"]:
        clone = item["_source"].copy()
        clone["document_id"] = item[u"_id"]
        modifiedResults.append(clone)

    return modifiedResults
