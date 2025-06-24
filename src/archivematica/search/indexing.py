import logging
import os
import sys
import time

from elasticsearch.helpers import bulk

from archivematica.archivematicaCommon import version
from archivematica.archivematicaCommon.aip_mets_parser import AIPMETSParser
from archivematica.dashboard.main.models import File
from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import DOC_TYPE
from archivematica.search.constants import ES_FIELD_ACCESSION_IDS
from archivematica.search.constants import ES_FIELD_AICCOUNT
from archivematica.search.constants import ES_FIELD_AICID
from archivematica.search.constants import ES_FIELD_CREATED
from archivematica.search.constants import ES_FIELD_ENCRYPTED
from archivematica.search.constants import ES_FIELD_FILECOUNT
from archivematica.search.constants import ES_FIELD_LOCATION
from archivematica.search.constants import ES_FIELD_NAME
from archivematica.search.constants import ES_FIELD_SIZE
from archivematica.search.constants import ES_FIELD_STATUS
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import STATUS_UPLOADED
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.constants import TRANSFERS_INDEX
from archivematica.search.exceptions import EmptySearchResultError
from archivematica.search.exceptions import TooManyResultsError
from archivematica.search.querying import _document_ids_from_field_query
from archivematica.search.utils import _try_to_index
from archivematica.search.utils import _wait_for_cluster_yellow_status

logger = logging.getLogger("archivematica.search")


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
