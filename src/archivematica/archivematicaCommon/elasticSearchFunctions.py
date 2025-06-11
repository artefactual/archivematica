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
import logging
import os
import sys
import time

from django.db.models import Q
from elasticsearch import Elasticsearch
from elasticsearch import ImproperlyConfigured
from elasticsearch.helpers import bulk

from archivematica.archivematicaCommon import version
from archivematica.archivematicaCommon.aip_mets_parser import AIPMETSParser
from archivematica.dashboard.main.models import File

logger = logging.getLogger("archivematica.common")

STATUS_DELETE_REQUESTED = "DEL_REQ"
STATUS_DELETED = "DELETED"
STATUS_UPLOADED = "UPLOADED"

AIPS_INDEX = "aips"
AIP_FILES_INDEX = "aipfiles"
TRANSFERS_INDEX = "transfers"
TRANSFER_FILES_INDEX = "transferfiles"

ES_FIELD_AICID = "AICID"
ES_FIELD_ACCESSION_IDS = "accessionids"
ES_FIELD_AICCOUNT = "countAIPsinAIC"
ES_FIELD_CREATED = "created"
ES_FIELD_ENCRYPTED = "encrypted"
ES_FIELD_FILECOUNT = "file_count"
ES_FIELD_LOCATION = "location"
ES_FIELD_NAME = "name"
ES_FIELD_SIZE = "size"
ES_FIELD_STATUS = "status"
ES_FIELD_UUID = "uuid"


class ElasticsearchError(Exception):
    """Not operational errors."""

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
INDEXES = [AIPS_INDEX, AIP_FILES_INDEX, TRANSFERS_INDEX, TRANSFER_FILES_INDEX]
# A doc type is still required in ES 6.x but it's limited to one per index.
# It will be removed in ES 7.x, so we'll use the same for all indexes.
DOC_TYPE = "_doc"
# Maximun ES result window. Use the scroll API for a better way to get all
# results or change `index.max_result_window` on each index settings.
MAX_QUERY_SIZE = 10000
# Maximun amount of fields per index (increased from the ES default of 1000).
TOTAL_FIELDS_LIMIT = 10000
# Maximum index depth (increased from the ES default of 20). The way the
# `structMap` element from the METS file is parsed may create a big depth
# in documents for AIPs with a big directories hierarchy.
DEPTH_LIMIT = 1000


def setup(hosts, timeout=DEFAULT_TIMEOUT, enabled=(AIPS_INDEX, TRANSFERS_INDEX)):
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
    if AIPS_INDEX in enabled:
        indexes.extend([AIPS_INDEX, AIP_FILES_INDEX])
    if TRANSFERS_INDEX in enabled:
        indexes.extend([TRANSFERS_INDEX, TRANSFER_FILES_INDEX])
    if len(indexes) > 0:
        create_indexes_if_needed(_es_client, indexes)
    else:
        logger.warning("Setting up the Elasticsearch client without enabled indexes.")


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
        except Exception:
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
    """Get settings and mappings for `aips` index.

    The mapping is dynamic and not a full representation of the final documents.
    For example, the AIP directories AMD and DMD sections are parsed from the
    METS file and added to a `transferMetadata` field.
    """
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "date_detection": False,
                "properties": {
                    ES_FIELD_NAME: {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    ES_FIELD_SIZE: {"type": "double"},
                    ES_FIELD_UUID: {"type": "keyword"},
                    ES_FIELD_ACCESSION_IDS: {"type": "keyword"},
                    ES_FIELD_STATUS: {"type": "keyword"},
                    ES_FIELD_FILECOUNT: {"type": "integer"},
                    ES_FIELD_LOCATION: {"type": "keyword"},
                },
            }
        },
    }


def _get_aipfiles_index_body():
    """Get settings and mappings for `aipfiles` index.

    The mapping is dynamic and not a full representation of the final documents.
    For example, the files AMD and DMD sections are parsed from the METS file
    and added to a `METS` field.
    """
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
                    ES_FIELD_AICID: {"type": "keyword"},
                    "indexedAt": {"type": "double"},
                    "filePath": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "fileExtension": {"type": "text"},
                    "origin": {"type": "text"},
                    "identifiers": {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
                    ES_FIELD_STATUS: {"type": "keyword"},
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
                    ES_FIELD_NAME: {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    ES_FIELD_STATUS: {"type": "text"},
                    "ingest_date": {"type": "date", "format": "dateOptionalTime"},
                    ES_FIELD_SIZE: {"type": "long"},
                    ES_FIELD_FILECOUNT: {"type": "integer"},
                    ES_FIELD_UUID: {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
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
                    ES_FIELD_STATUS: {"type": "keyword"},
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
                    ES_FIELD_CREATED: {"type": "double"},
                    ES_FIELD_SIZE: {"type": "double"},
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
                    "pending_deletion": {"type": "boolean"},
                }
            }
        },
    }


def _get_index_settings():
    """Returns a dictionary with the settings used in all indexes."""
    return {
        "index": {
            "mapping": {
                "total_fields": {"limit": TOTAL_FIELDS_LIMIT},
                "depth": {"limit": DEPTH_LIMIT},
            },
            "analysis": {
                "analyzer": {
                    # Use the char_group tokenizer to split paths and filenames,
                    # including file extensions, which avoids the overhead of
                    # the pattern tokenizer.
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
            },
        }
    }


# ---------------
# INDEX RESOURCES
# ---------------


def index_aip_and_files(
    client,
    uuid,
    aip_stored_path,
    mets_staging_path,
    name,
    aip_size,
    aips_in_aic=None,
    identifiers=None,
    encrypted=False,
    location="",
    printfn=print,
    dashboard_uuid="",
):
    """Index AIP and AIP files with UUID `uuid` at path `path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the AIP we're indexing.
    :param aip_stored_path: path on disk where the AIP is located.
    :param mets_staging_path: path on disk where the AIP METS file is located.
    :param name: AIP name.
    :param aip_size: AIP size.
    :param aips_in_aic: optional number of AIPs stored in AIC.
    :param identifiers: optional additional identifiers (MODS, Islandora, etc.).
    :param encrypted: optional AIP encrypted boolean (defaults to `False`).
    :param printfn: optional print funtion.
    :param dashboard_uuid: Pipeline UUID.
    :return: 0 is succeded, 1 otherwise.
    """
    # Stop if METS file is not at staging path.
    error_message = None
    if not os.path.exists(mets_staging_path):
        error_message = "METS file does not exist at: " + mets_staging_path
    if error_message:
        logger.error(error_message)
        printfn(error_message, file=sys.stderr)
        return 1

    parser = AIPMETSParser(mets_staging_path)

    if identifiers is None:
        identifiers = []

    printfn("AIP UUID: " + uuid)
    printfn("Indexing AIP files ...")

    (files_indexed, accession_ids) = _index_aip_files(
        client=client,
        uuid=uuid,
        name=name,
        identifiers=identifiers,
        dashboard_uuid=dashboard_uuid,
        parser=parser,
    )

    printfn("Files indexed: " + str(files_indexed))
    printfn("Indexing AIP ...")

    aip_data = {
        ES_FIELD_UUID: uuid,
        ES_FIELD_NAME: name,
        "filePath": aip_stored_path,
        ES_FIELD_SIZE: int(aip_size) / (1024 * 1024),
        ES_FIELD_FILECOUNT: files_indexed,
        "origin": dashboard_uuid,
        ES_FIELD_CREATED: parser.created,
        ES_FIELD_AICID: parser.aic_identifier,
        "isPartOf": parser.is_part_of,
        ES_FIELD_AICCOUNT: aips_in_aic,
        "identifiers": identifiers,
        "transferMetadata": parser.aip_metadata,
        ES_FIELD_ENCRYPTED: encrypted,
        ES_FIELD_ACCESSION_IDS: accession_ids,
        ES_FIELD_STATUS: STATUS_UPLOADED,
        ES_FIELD_LOCATION: location,
    }

    _wait_for_cluster_yellow_status(client)
    _try_to_index(client, aip_data, AIPS_INDEX, printfn=printfn)
    printfn("Done.")

    return 0


def _index_aip_files(
    client, uuid, name, identifiers=None, dashboard_uuid="", parser=None
):
    """Index AIP files from AIP with UUID `uuid` and METS at path `mets_path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the AIP we're indexing.
    :param name: AIP name.
    :param identifiers: optional additional identifiers (MODS, Islandora, etc.).
    :param dashboard_uuid: Pipeline UUID.
    :param parser: AIPMETSParser instance.
    :return: number of files indexed, list of accession numbers
    """

    if identifiers is None:
        identifiers = []

    # Use a set to ensure accession numbers are unique without needing to
    # iterate through the list each time to check.
    accession_ids = set()

    am_version = version.get_version()
    indexed_at = time.time()

    def _generator():
        # Index AIC METS file if it exists.
        for file_data, file_accession_ids in parser.files():
            file_data.update(
                {
                    "archivematicaVersion": am_version,
                    "AIPUUID": uuid,
                    "sipName": name,
                    "indexedAt": indexed_at,
                    "isPartOf": parser.is_part_of,
                    ES_FIELD_AICID: parser.aic_identifier,
                    "origin": dashboard_uuid,
                    ES_FIELD_STATUS: STATUS_UPLOADED,
                }
            )
            file_data["transferMetadata"] = (
                parser.aip_metadata + file_data["transferMetadata"]
            )
            file_data["identifiers"] = identifiers + file_data["identifiers"]
            accession_ids.update(file_accession_ids)

            yield {
                "_op_type": "index",
                "_index": AIP_FILES_INDEX,
                "_type": DOC_TYPE,
                "_source": file_data,
            }

    # Number of docs (chunk_size) defaults to 500 which is probably too big as
    # we're potentially dealing with large documents (full amdSec embedded).
    # It should be revisited once we make documents smaller.
    bulk(client, _generator(), chunk_size=50)

    file_count = parser.file_count
    accession_ids_list = list(accession_ids)

    return (file_count, accession_ids_list)


def index_transfer_and_files(
    client,
    uuid,
    path,
    size,
    pending_deletion=False,
    printfn=print,
    dashboard_uuid="",
    transfer_name="",
    accession_id="",
    ingest_date="",
):
    """Indexes Transfer and Transfer files with UUID `uuid` at path `path`.

    :param client: The ElasticSearch client.
    :param uuid: The UUID of the transfer we're indexing.
    :param path: path on disk, including the transfer directory and a
                 trailing / but not including objects/.
    :param size: size of transfer in bytes.
    :param printfn: optional print funtion.
    :param dashboard_uuid: Pipeline UUID.
    :param transfer_name: name of Transfer
    :param accession_id: optional accession ID
    :param ingest_date: date Transfer was indexed
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
        client,
        uuid,
        path,
        transfer_name,
        accession_id,
        ingest_date,
        pending_deletion=pending_deletion,
        status=status,
        printfn=printfn,
        dashboard_uuid=dashboard_uuid,
    )

    printfn("Files indexed: " + str(files_indexed))
    printfn("Indexing Transfer ...")

    transfer_data = {
        ES_FIELD_NAME: transfer_name,
        ES_FIELD_STATUS: status,
        "accessionid": accession_id,
        "ingest_date": ingest_date,
        ES_FIELD_FILECOUNT: files_indexed,
        ES_FIELD_SIZE: int(size),
        ES_FIELD_UUID: uuid,
        "pending_deletion": pending_deletion,
    }

    _wait_for_cluster_yellow_status(client)
    _try_to_index(client, transfer_data, TRANSFERS_INDEX, printfn=printfn)
    printfn("Done.")

    return 0


def _index_transfer_files(
    client,
    uuid,
    path,
    transfer_name,
    accession_id,
    ingest_date,
    status="",
    pending_deletion=False,
    printfn=print,
    dashboard_uuid="",
):
    """Indexes files in the Transfer with UUID `uuid` at path `path`.

    :param client: ElasticSearch client.
    :param uuid: UUID of the Transfer in the DB.
    :param path: path on disk, including the transfer directory and a
                 trailing / but not including objects/.
    :param transfer_name: name of Transfer
    :param accession_id: optional accession ID
    :param ingest_date: date Transfer was indexed
    :param status: optional Transfer status.
    :param printfn: optional print funtion.
    :param dashboard_uuid: Pipeline UUID.
    :return: number of files indexed.
    """
    files_indexed = 0

    # Some files should not be indexed.
    # This should match the basename of the file.
    ignore_files = ["processingMCP.xml"]

    for filepath in _list_files_in_dir(path):
        if os.path.isfile(filepath):
            # Get file path info
            stripped_path = filepath.replace(path, transfer_name + "/")
            filename = os.path.basename(filepath)

            if filename in ignore_files:
                printfn(f"Skipping indexing {stripped_path}")
                continue

            indexData = get_transfer_file_index_data(filepath, path, uuid)
            indexData.update(
                {
                    "filename": filename,
                    "relative_path": stripped_path,
                    "sipuuid": uuid,
                    "accessionid": accession_id,
                    ES_FIELD_STATUS: status,
                    "origin": dashboard_uuid,
                    "ingestdate": ingest_date,
                    "tags": [],
                    "pending_deletion": pending_deletion,
                }
            )

            printfn(
                f"Indexing {indexData['relative_path']} (UUID: {indexData['fileuuid']})"
            )

            _wait_for_cluster_yellow_status(client)
            _try_to_index(client, indexData, TRANSFER_FILES_INDEX, printfn=printfn)

            files_indexed = files_indexed + 1

    return files_indexed


def get_transfer_file_index_data(filepath, transfer_path, uuid):
    # We need to account for the possibility of dealing with a BagIt
    # transfer package - the new default in Archivematica.
    # The BagIt is created when the package is sent to backlog hence
    # the locations in the database do not reflect the BagIt paths.
    # Strip the "data/" part when looking up the file entry.
    currentlocation = "%transferDirectory%" + os.path.relpath(
        filepath, transfer_path
    ).removeprefix("data/")
    try:
        f = File.objects.get(currentlocation=currentlocation.encode(), transfer_id=uuid)
        file_uuid = str(f.uuid)
        formats = _get_file_formats(f)
        bulk_extractor_reports = _list_bulk_extractor_reports(transfer_path, file_uuid)
        if f.modificationtime is not None:
            modification_date = f.modificationtime.strftime("%Y-%m-%d")
        else:
            modification_date = ""
    except File.DoesNotExist:
        file_uuid, modification_date = "", ""
        formats = []
        bulk_extractor_reports = []

    file_extension = os.path.splitext(filepath)[1][1:].lower()

    # Size in megabytes
    size = os.path.getsize(filepath) / (1024 * 1024)
    create_time = os.stat(filepath).st_ctime

    # TODO: Index Backlog Location UUID?
    return {
        "fileuuid": file_uuid,
        ES_FIELD_CREATED: create_time,
        "modification_date": modification_date,
        ES_FIELD_SIZE: size,
        "file_extension": file_extension,
        "bulk_extractor_reports": bulk_extractor_reports,
        "format": formats,
    }


def _try_to_index(
    client, data, index, wait_between_tries=10, max_tries=10, printfn=print
):
    exception = None
    if max_tries < 1:
        raise ValueError("max_tries must be 1 or greater")
    for _ in range(0, max_tries):
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


def _get_file_formats(f):
    formats = []
    fields = [
        "format_version__pronom_id",
        "format_version__description",
        "format_version__format__group__description",
    ]
    for puid, fmt, group in f.fileformatversion_set.all().values_list(*fields):
        formats.append({"puid": puid, "format": fmt, "group": group})

    return formats


def _list_bulk_extractor_reports(transfer_path, file_uuid):
    reports = []
    log_path = os.path.join(transfer_path, "data", "logs", "bulk-" + file_uuid)

    if not os.path.isdir(log_path):
        return reports
    for report in ["telephone", "ccn", "ccn_track2", "pii"]:
        path = os.path.join(log_path, report + ".txt")
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            reports.append(report)

    return reports


def _list_files_in_dir(path, filepaths=None):
    if filepaths is None:
        filepaths = []

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
            "Number of items in backlog (%s) exceeds maximum amount fetched (%s)",
            results["hits"]["total"],
            MAX_QUERY_SIZE,
        )
    return results


def get_aip_data(client, uuid, fields=None):
    search_params = {
        "body": {"query": {"term": {ES_FIELD_UUID: uuid}}},
        "index": AIPS_INDEX,
    }

    if fields:
        search_params["_source"] = fields

    aips = client.search(**search_params)

    return aips["hits"]["hits"][0]


def get_aipfile_data(client, uuid, fields=None):
    search_params = {
        "body": {"query": {"term": {"FILEUUID": uuid}}},
        "index": AIP_FILES_INDEX,
    }

    if fields:
        search_params["_source"] = fields

    aipfiles = client.search(**search_params)

    return aipfiles["hits"]["hits"][0]


def _document_ids_from_field_query(client, index, field, value):
    document_ids = []

    # Escape /'s with \\
    searchvalue = str(value).replace("/", "\\/")
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

    results = client.search(body=query, index=TRANSFER_FILES_INDEX, _source="tags")

    count = results["hits"]["total"]
    if count == 0:
        raise EmptySearchResultError(f"No matches found for file with UUID {uuid}")
    if count > 1:
        raise TooManyResultsError(
            f"{count} matches found for file with UUID {uuid}; unable to fetch a single result"
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
        client, TRANSFER_FILES_INDEX, "fileuuid", uuid
    )

    count = len(document_ids)
    if count == 0:
        raise EmptySearchResultError(f"No matches found for file with UUID {uuid}")
    if count > 1:
        raise TooManyResultsError(
            f"{count} matches found for file with UUID {uuid}; unable to fetch a single result"
        )

    body = {"doc": {"tags": tags}}
    client.update(
        body=body, index=TRANSFER_FILES_INDEX, doc_type=DOC_TYPE, id=document_ids[0]
    )
    return True


def get_transfer_file_info(client, field, value):
    """
    Get transferfile information from ElasticSearch with query field = value.
    """
    logger.debug("get_transfer_file_info: field: %s, value: %s", field, value)
    results = {}
    query = {"query": {"term": {field: value}}}
    documents = search_all_results(client, body=query, index=TRANSFER_FILES_INDEX)
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
    _delete_matching_documents(client, TRANSFERS_INDEX, ES_FIELD_UUID, uuid)


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
                client, TRANSFER_FILES_INDEX, "sipuuid", transfer
            )
            if len(files) > 0:
                for file_id in files:
                    client.delete(
                        index=TRANSFER_FILES_INDEX, doc_type=DOC_TYPE, id=file_id
                    )
    else:
        if not unit_type:
            unit_type = "transfer or SIP"
        logger.warning("No transfers found for %s %s", unit_type, uuid)


def delete_aip(client, uuid):
    _delete_matching_documents(client, AIPS_INDEX, ES_FIELD_UUID, uuid)


def delete_aip_files(client, uuid):
    _delete_matching_documents(client, AIP_FILES_INDEX, "AIPUUID", uuid)


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
    document_id = _document_id_from_field_query(client, index, ES_FIELD_UUID, uuid)

    if document_id is None:
        logger.error(f"Unable to find document with UUID {uuid} in index {index}")
        return

    client.update(
        body={"doc": {field: value}}, index=index, doc_type=DOC_TYPE, id=document_id
    )


def mark_aip_stored(client, uuid):
    _update_field(client, AIPS_INDEX, uuid, ES_FIELD_STATUS, STATUS_UPLOADED)


def mark_aip_deletion_requested(client, uuid):
    """Update AIP package and file indices to reflect AIP deletion request.

    :param client: ES client.
    :param uuid: AIP UUID.
    :return: None.
    """
    _update_field_for_package_and_files(
        client, AIPS_INDEX, AIP_FILES_INDEX, "AIPUUID", uuid, ES_FIELD_STATUS, "DEL_REQ"
    )


def mark_backlog_deletion_requested(client, uuid):
    """Update transfer package and file indices to reflect backlog deletion request.

    :param client: ES client.
    :param uuid: Transfer UUID.
    :return: None.
    """
    _update_field_for_package_and_files(
        client,
        TRANSFERS_INDEX,
        TRANSFER_FILES_INDEX,
        "sipuuid",
        uuid,
        "pending_deletion",
        True,
    )


def revert_aip_deletion_request(client, uuid):
    """Update AIP indices to reflect rejected deletion request

    :param client: ES client.
    :param uuid: AIP UUID.
    :returns: None.
    """
    _update_field_for_package_and_files(
        client,
        AIPS_INDEX,
        AIP_FILES_INDEX,
        "AIPUUID",
        uuid,
        ES_FIELD_STATUS,
        STATUS_UPLOADED,
    )


def revert_backlog_deletion_request(client, uuid):
    """Update transfer indices to reflect rejected deletion request

    :param client: ES client.
    :param uuid: Transfer UUID.
    :returns: None.
    """
    _update_field_for_package_and_files(
        client,
        TRANSFERS_INDEX,
        TRANSFER_FILES_INDEX,
        "sipuuid",
        uuid,
        "pending_deletion",
        False,
    )


def _update_field_for_package_and_files(
    client, package_index, files_index, package_uuid_field, package_uuid, field, value
):
    """Update the specified field for a package and its related files

    :param client: ES client.
    :param package_index: Name of package index to update.
    :param files_index: Name of files index to update.
    :param package_uuid_field: Name of ES field for package UUID in package_index.
    :param package_uuid: UUID of package to update.
    :param field: Field in indices to update.
    :param value: Value to set in updated field.
    :return: None.
    """
    _update_field(client, package_index, package_uuid, field, value)

    files = _document_ids_from_field_query(
        client, files_index, package_uuid_field, package_uuid
    )
    for file_id in files:
        client.update(
            body={"doc": {field: value}},
            index=files_index,
            doc_type=DOC_TYPE,
            id=file_id,
        )


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
        clone["document_id"] = item["_id"]
        modifiedResults.append(clone)

    return modifiedResults
