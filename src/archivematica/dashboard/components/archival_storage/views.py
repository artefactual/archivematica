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
import csv
import json
import logging
import os
import uuid
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware
from django.utils.translation import gettext as _

import archivematica.search.constants
from archivematica.archivematicaCommon import databaseFunctions
from archivematica.archivematicaCommon import storageService as storage_service
from archivematica.archivematicaCommon.archivematicaFunctions import (
    AMCLIENT_ERROR_CODES,
)
from archivematica.archivematicaCommon.archivematicaFunctions import setup_amclient
from archivematica.dashboard.components import advanced_search
from archivematica.dashboard.components import helpers
from archivematica.dashboard.components.archival_storage import forms
from archivematica.dashboard.components.archival_storage.atom import (
    AtomMetadataUploadError,
)
from archivematica.dashboard.components.archival_storage.atom import (
    upload_dip_metadata_to_atom,
)
from archivematica.search.service import AIPNotFoundError
from archivematica.search.service import SortSpec
from archivematica.search.service import setup_search_service_from_conf

logger = logging.getLogger("archivematica.dashboard")

AIPSTOREPATH = "/var/archivematica/sharedDirectory/www/AIPsStore"

AIP_STATUS_DESCRIPTIONS = {
    archivematica.search.constants.STATUS_UPLOADED: _("Stored"),
    archivematica.search.constants.STATUS_DELETE_REQUESTED: _("Deletion requested"),
}

DIRECTORY_PERMISSIONS = 0o770
FILE_PERMISSIONS = 0o660

CSV_MIMETYPE = "text/csv"


def sync_es_aip_status_with_storage_service(uuid, es_status):
    """Update AIP's status in ES indices to match Storage Service.

    This is a bit of a kludge that is made necessary by the fact that
    the Storage Service does not update ElasticSearch directly when
    a package's status has changed.

    Updates to ES are visible in Archival Storage after running a new
    search or refreshing the page.

    :param uuid: AIP UUID.
    :param es_status: Current package status in ES.

    :returns: Boolean indicating whether AIP should be kept in search
    results (i.e. has not been deleted from Storage Service).
    """
    keep_in_results = True

    amclient = setup_amclient()
    amclient.package_uuid = uuid
    api_results = amclient.get_package_details()

    if api_results in AMCLIENT_ERROR_CODES:
        logger.warning(
            f"Package {uuid} not found in Storage Service. AMClient error code: {api_results}"
        )
        return keep_in_results

    aip_status = api_results.get("status")

    if not aip_status:
        logger.warning(
            "Status for package {} could not be retrived from Storage Service."
        )
        return keep_in_results

    search_service = setup_search_service_from_conf(settings)
    if (
        aip_status == archivematica.search.constants.STATUS_DELETE_REQUESTED
        and es_status != archivematica.search.constants.STATUS_DELETE_REQUESTED
    ):
        search_service.mark_aip_for_deletion(uuid)
    elif (
        aip_status == archivematica.search.constants.STATUS_UPLOADED
        and es_status != archivematica.search.constants.STATUS_UPLOADED
    ):
        search_service.unmark_aip_for_deletion(uuid)
    elif aip_status == archivematica.search.constants.STATUS_DELETED:
        keep_in_results = False
        search_service.delete_aip(uuid)
        search_service.delete_aip_files(uuid)

    return keep_in_results


def execute(request):
    """Remove any deleted AIPs from ES index and render main archival storage page.

    :param request: Django request object.
    :return: The main archival storage page rendered.
    """
    if archivematica.search.constants.AIPS_INDEX in settings.SEARCH_ENABLED:
        search_service = setup_search_service_from_conf(settings)

        total_size = total_size_of_aips(search_service)
        aip_indexed_file_count = aip_file_count(search_service)

        return render(
            request,
            "archival_storage/archival_storage.html",
            {
                "total_size": total_size,
                "aip_indexed_file_count": aip_indexed_file_count,
            },
        )

    return render(request, "archival_storage/archival_storage.html")


def get_es_property_from_column_index(index, file_mode):
    """Get ES document property name corresponding to column index in DataTable.

    When the user clicks a column header in the data table, we'll receive info
    in the AJAX request telling us which column # we're supposed to sort across
    in our query. This function will translate the column index to the
    corresponding property name we'll tell ES to sort on.

    :param index: The column index that the data table says we're sorting on.
    :param file_mode: Whether we're looking at transfers or transfer files.
    :return: The ES document property name corresponding to the column index.
    """
    table_columns = (
        (
            "name.raw",
            "uuid",
            "AICID",
            "size",
            "file_count",
            "accessionids",
            "created",
            "status",
            "encrypted",
            "location",
            None,
        ),  # AIPS are being displayed
        (
            None,
            "filePath.raw",
            "FILEUUID",
            "sipName.raw",
            "accessionid",
            "status",
            None,
        ),  # AIP files are being displayed
    )

    if index < 0 or index >= len(table_columns[file_mode]):
        logger.warning(
            "Archival Storage column index specified is invalid for sorting, got %s",
            index,
        )
        index = 0

    return table_columns[file_mode][index]


# Ordered dict from es fields.
#
# Archivematica code currently uses a mix of snake case, camel case,
# and other inconsistent variants of both for its Elasticsearch
# field names. Here we create a mapping to enable their output to
# something nice to read. We can also use this dictionary to guarantee
# the field output ordering and make sure that the fields output are
# translatable.
_ORDERED_DICT_ES_FIELDS = OrderedDict(
    [
        (archivematica.search.constants.ES_FIELD_NAME, _("Name")),
        (archivematica.search.constants.ES_FIELD_UUID, _("UUID")),
        (archivematica.search.constants.ES_FIELD_AICID, _("AICID")),
        (archivematica.search.constants.ES_FIELD_AICCOUNT, _("Count AIPs in AIC")),
        ("bytes", _("Bytes")),
        (archivematica.search.constants.ES_FIELD_SIZE, _("Size")),
        (archivematica.search.constants.ES_FIELD_FILECOUNT, _("File count")),
        (archivematica.search.constants.ES_FIELD_ACCESSION_IDS, _("Accession IDs")),
        (archivematica.search.constants.ES_FIELD_CREATED, _("Created date (UTC)")),
        (archivematica.search.constants.ES_FIELD_STATUS, _("Status")),
        ("type", _("Type")),
        (archivematica.search.constants.ES_FIELD_ENCRYPTED, _("Encrypted")),
        (archivematica.search.constants.ES_FIELD_LOCATION, _("Location")),
    ]
)


def generate_search_as_csv_rows(csvwriter, es_results):
    """CSV header and rows generator function.

    This function yields CSV rows efficiently in the context of HTTP streaming.
    The structure of the document is determined by ``_ORDERED_DICT_ES_FIELDS``.
    """
    # Header.
    yield csvwriter.writerow(_ORDERED_DICT_ES_FIELDS.values())

    # Rows.
    keys = _ORDERED_DICT_ES_FIELDS.keys()
    current_timezone = get_current_timezone()
    for item in es_results:
        row = OrderedDict((key, item.get(key)) for key in keys)

        # Normalize accession identifiers.
        try:
            accession_ids = "; ".join(
                row[archivematica.search.constants.ES_FIELD_ACCESSION_IDS]
            )
        except TypeError:
            accession_ids = row[archivematica.search.constants.ES_FIELD_ACCESSION_IDS]
        row[archivematica.search.constants.ES_FIELD_ACCESSION_IDS] = accession_ids

        # Localize date output.
        try:
            created = make_aware(
                datetime.fromtimestamp(
                    row[archivematica.search.constants.ES_FIELD_CREATED]
                ),
                timezone=current_timezone,
            )
        except TypeError:
            created = row[archivematica.search.constants.ES_FIELD_CREATED]
        row[archivematica.search.constants.ES_FIELD_CREATED] = created

        yield csvwriter.writerow(list(row.values()))


def search_as_csv(es_results, file_name):
    class echo:
        """File-like object that returns the value written."""

        def write(self, value):
            return value

    writer = csv.writer(echo(), quoting=csv.QUOTE_ALL, lineterminator="\n")
    response = StreamingHttpResponse(
        generate_search_as_csv_rows(writer, es_results),
        content_type=CSV_MIMETYPE,
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    response["Content-Type"] = "{}; charset={}".format(CSV_MIMETYPE, "utf-8")

    return response


def _search_aip_files(
    query: dict,
    search_service,
    start: int,
    page_size: int,
    order_by: str,
    sort_direction: str,
) -> tuple:
    """
    Execute Elasticsearch search for AIP files using search service.

    :param query: The Elasticsearch query to execute
    :param search_service: The search service instance
    :param start: Start index for pagination
    :param page_size: Number of results per page
    :param order_by: Field to sort by
    :param sort_direction: Sort direction (asc/desc)
    :return: Tuple of (hits, hit_count)
    """
    sort_param = SortSpec(field=order_by, order=sort_direction) if order_by else None
    fields = ["filePath", "FILEUUID", "AIPUUID", "accessionid", "status"]

    hits = search_service.search_aip_files(
        query=query, size=page_size, from_=start, sort=sort_param, fields=fields
    )
    hit_count = hits["hits"]["total"]["value"]
    return hits, hit_count


def _search_aips(
    query: dict,
    search_service,
    start: int,
    page_size: int,
    order_by: str,
    sort_direction: str,
) -> tuple:
    """
    Execute Elasticsearch search for AIPs.

    :param query: The Elasticsearch query to execute
    :param search_service: The search service instance
    :param start: Start index for pagination
    :param page_size: Number of results per page
    :param order_by: Field to sort by
    :param sort_direction: Sort direction (asc/desc)
    :return: Tuple of (hits, hit_count)
    """
    # AIP mode:
    # Query to aipfiles, but only fetch & aggregate AIP UUIDs.
    # Based on AIP UUIDs, query to aips.
    # ES query will limit to 10 aggregation results by default,
    # add size parameter in terms to override.
    # TODO: Use composite aggregation when it gets out of beta.
    query["aggs"] = {
        "aip_uuids": {
            "terms": {
                "field": "AIPUUID",
                "size": str(settings.ELASTICSEARCH_MAX_QUERY_SIZE),
            }
        }
    }
    hits = search_service.search_aip_files(query, size=0)
    buckets = hits.get("aggregations", {}).get("aip_uuids", {}).get("buckets", [])
    uuids = [bucket["key"] for bucket in buckets]
    uuid_file_counts = {bucket["key"]: bucket["doc_count"] for bucket in buckets}

    # If no AIPs found, return empty result
    if not uuids:
        empty_result = {"hits": {"hits": [], "total": 0}}
        return empty_result, 0, {}

    # Recreate query to search over AIPs
    aip_query = {"query": {"terms": {"uuid": uuids}}}
    sort_param = SortSpec(field=order_by, order=sort_direction) if order_by else None
    fields = [
        "name",
        "uuid",
        "size",
        "accessionids",
        "created",
        "status",
        "encrypted",
        "AICID",
        "isPartOf",
        "countAIPsinAIC",
        "location",
    ]

    hits = search_service.search_aips(
        query=aip_query,
        size=page_size,
        from_=start,
        sort=sort_param,
        fields=fields,
    )
    hit_count = hits["hits"]["total"]["value"]
    return hits, hit_count, uuid_file_counts


def search(request):
    """A JSON end point that returns results for AIPs and their files.

    :param request: Django request object.
    :return: A JSON object including required metadata for the datatable and
    the search results.
    """
    REQUEST_FILE = "requestFile"
    MIMETYPE = "mimeType"
    RETURN_ALL = "returnAll"
    FILE_NAME = "fileName"

    request_file = request.GET.get(REQUEST_FILE, "").lower() == "true"
    file_mime = request.GET.get(MIMETYPE, "")
    file_name = request.GET.get(FILE_NAME, "archival-storage-report.csv")

    if request_file and file_mime != CSV_MIMETYPE:
        return HttpResponse(f"Please use ?mimeType={CSV_MIMETYPE}", status=400)

    # Configure page-size requirements for the search.
    DEFAULT_PAGE_SIZE = 10
    page_size = None
    if request.GET.get(RETURN_ALL, "").lower() == "true":
        page_size = archivematica.search.constants.MAX_QUERY_SIZE
    if page_size is None:
        page_size = int(request.GET.get("iDisplayLength", DEFAULT_PAGE_SIZE))

    # Get search parameters from the request.
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    if "query" not in request.GET:
        queries, ops, fields, types = (["*"], ["or"], [""], ["term"])
    # Use "indexedAt" field in aipfiles index for date range queries.
    # This works for AIPs as well because of how AIP UUIDs are collected by
    # first searching the aipfiles index.
    if types[0] == "range":
        fields = ["indexedAt"]
    query = advanced_search.assemble_query(queries, ops, fields, types)
    file_mode = request.GET.get("file_mode") == "true"

    # Configure other aspects of the search including starting page and sort
    # order.
    start = int(request.GET.get("iDisplayStart", 0))
    order_by = get_es_property_from_column_index(
        int(request.GET.get("iSortCol_0", 0)), file_mode
    )
    sort_direction = request.GET.get("sSortDir_0", "asc")

    search_service = setup_search_service_from_conf(settings)

    try:
        if file_mode:
            results, hit_count = _search_aip_files(
                query, search_service, start, page_size, order_by, sort_direction
            )
            augmented_results = search_augment_file_results(search_service, results)
        else:
            results, hit_count, uuid_file_counts = _search_aips(
                query, search_service, start, page_size, order_by, sort_direction
            )
            augmented_results = search_augment_aip_results(results, uuid_file_counts)

        if request_file and not file_mode:
            return search_as_csv(augmented_results, file_name=file_name)

        return helpers.json_response(
            {
                "iTotalRecords": hit_count,
                "iTotalDisplayRecords": hit_count,
                "sEcho": int(
                    request.GET.get("sEcho", 0)
                ),  # It was recommended we convert sEcho to int to prevent XSS.
                "aaData": augmented_results,
            }
        )

    except Exception:
        err_desc = "Error accessing AIPs index"
        logger.exception(err_desc)
        return HttpResponse(err_desc)


def search_augment_aip_results(raw_results, counts):
    """Augment AIP results and update ES status if AIP is pending deletion.

    We perform sync_es_aip_status_with_storage_service routine here to avoid
    needing to iterate through all of the results a second time.

    :param raw_results: Raw results returned from ES.
    :param counts: Count of file UUIDs associated with AIP.

    :return: Augmented and formatted results.
    """
    modified_results = []

    for item in raw_results["hits"]["hits"]:
        fields = item["_source"]
        new_item = {
            "name": fields.get("name", ""),
            "uuid": fields.get("uuid", ""),
            "file_count": counts.get(fields.get("uuid"), 0),
            "created": fields.get("created", 0),
            "isPartOf": fields.get("isPartOf"),
            "AICID": fields.get("AICID"),
            "countAIPsinAIC": fields.get("countAIPsinAIC", "(unknown)"),
            "status": AIP_STATUS_DESCRIPTIONS[
                fields.get("status", archivematica.search.constants.STATUS_UPLOADED)
            ],
            "encrypted": fields.get("encrypted", False),
            "accessionids": fields.get("accessionids", []),
            "location": fields.get("location", ""),
        }
        size = fields.get("size")
        if size is not None:
            bytecount = size * (1024 * 1024)
            new_item["bytes"] = bytecount
            new_item["size"] = filesizeformat(bytecount)

        aic_id = fields.get("AICID")
        if aic_id and "AIC#" in aic_id:
            new_item["type"] = "AIC"
        else:
            new_item["type"] = "AIP"

        status = fields.get("status")
        keep_in_results = True
        if status is not None:
            # Only return details for AIPs that haven't been deleted
            # from the Storage Service in the search results.
            keep_in_results = sync_es_aip_status_with_storage_service(
                fields["uuid"], status
            )

        if keep_in_results:
            modified_results.append(new_item)

    return modified_results


def search_augment_file_results(search_service, raw_results):
    """Augment file results.

    :param search_service: Search service instance.
    :param raw_results: Raw results returned from ES.

    :return: Augmented and formatted results.
    """
    modifiedResults = []

    for item in raw_results["hits"]["hits"]:
        if "_source" not in item:
            continue

        clone = item["_source"].copy()

        try:
            aip = search_service.get_aip_data(
                clone["AIPUUID"],
                fields=[
                    "uuid",
                    "name",
                    "filePath",
                    "size",
                    "origin",
                    "created",
                    "encrypted",
                ],
            )

            clone["sipname"] = aip["_source"]["name"]
            clone["fileuuid"] = clone["FILEUUID"]
            clone["href"] = aip["_source"]["filePath"].replace(
                AIPSTOREPATH + "/", "AIPsStore/"
            )

        except Exception:
            aip = None
            clone["sipname"] = False

        clone["status"] = AIP_STATUS_DESCRIPTIONS[
            clone.get("status", archivematica.search.constants.STATUS_UPLOADED)
        ]
        clone["filename"] = os.path.basename(clone["filePath"])
        clone["document_id"] = item["_id"]
        clone["document_id_no_hyphens"] = item["_id"].replace("-", "____")

        modifiedResults.append(clone)

    return modifiedResults


def create_aic(request):
    """Create an AIC from POSTed list of search params.

    :param request: Django request object.
    :return: Redirect to appropriate view.
    """

    if "query" not in request.GET:
        messages.error(request, "Unable to create AIC: No AIPs selected")
        return redirect("archival_storage:archival_storage_index")

    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    if types[0] == "range":
        fields = ["indexedAt"]
    query = advanced_search.assemble_query(queries, ops, fields, types)
    search_service = setup_search_service_from_conf(settings)

    try:
        query["aggs"] = {
            "aip_uuids": {
                "terms": {
                    "field": "AIPUUID",
                    "size": str(settings.ELASTICSEARCH_MAX_QUERY_SIZE),
                }
            }
        }
        results = search_service.search_aip_files(query, size=0)
        buckets = results["aggregations"]["aip_uuids"]["buckets"]
        aip_uuids = [bucket["key"] for bucket in buckets]

    except Exception:
        err_desc = "Error accessing AIPs index"
        logger.exception(err_desc)
        return HttpResponse(err_desc)

    logger.info(f"AIC AIP UUIDs: {aip_uuids}")

    # Use the AIP UUIDs to fetch names, which are used to produce files below.
    query = {"query": {"terms": {"uuid": aip_uuids}}}
    results = search_service.search_aips(
        query,
        fields=["uuid", "name"],
        size=archivematica.search.constants.MAX_QUERY_SIZE,
    )

    # Create SIP (AIC) directory in a staging directory.
    shared_dir = settings.SHARED_DIRECTORY
    staging_dir = os.path.join(shared_dir, "tmp")
    temp_uuid = str(uuid.uuid4())
    destination = os.path.join(staging_dir, temp_uuid)
    try:
        os.mkdir(destination)
        os.chmod(destination, DIRECTORY_PERMISSIONS)
    except OSError as e:
        messages.error(request, "Error creating AIC")
        logger.exception(f"Error creating AIC: {e}")
        return redirect("archival_storage:archival_storage_index")

    # Create an entry for the SIP (AIC) in the database.
    mcp_destination = os.path.join(destination.replace(shared_dir, "%sharedPath%"), "")
    databaseFunctions.createSIP(mcp_destination, UUID=temp_uuid, sip_type="AIC")

    # Create files with filename = AIP UUID, and contents = AIP name.
    for aip in results["hits"]["hits"]:
        filepath = os.path.join(destination, aip["_source"]["uuid"])
        with open(filepath, "w") as f:
            os.chmod(filepath, FILE_PERMISSIONS)
            f.write(str(aip["_source"]["name"]))

    return redirect("ingest:aic_metadata_add", temp_uuid)


def aip_download(request, uuid):
    redirect_url = storage_service.download_file_url(uuid)
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?"
    )


def aip_file_download(request, uuid):
    search_service = setup_search_service_from_conf(settings)

    # get AIP file properties
    aipfile = search_service.get_aipfile_data(
        uuid, fields=["filePath", "FILEUUID", "AIPUUID"]
    )

    # get file's AIP's properties
    sipuuid = aipfile["_source"]["AIPUUID"]
    aip = search_service.get_aip_data(
        sipuuid, fields=["uuid", "name", "filePath", "size", "origin", "created"]
    )
    aip_filepath = aip["_source"]["filePath"]

    # work out path components
    aip_archive_filename = os.path.basename(aip_filepath)

    # splittext doesn't deal with double extensions, so special-case .tar.bz2
    if aip_archive_filename.endswith(".tar.bz2"):
        subdir = aip_archive_filename[:-8]
    else:
        subdir = os.path.splitext(aip_archive_filename)[0]

    file_relative_path = os.path.join(subdir, "data", aipfile["_source"]["filePath"])

    redirect_url = storage_service.extract_file_url(
        aip["_source"]["uuid"], file_relative_path
    )
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?"
    )


def aip_mets_file_download(request, uuid):
    """Download an individual AIP METS file."""
    search_service = setup_search_service_from_conf(settings)
    try:
        aip = search_service.get_aip_data(uuid, fields=["name"])
    except AIPNotFoundError:
        # TODO: 404 settings for the project do not display this to the user (only DEBUG).
        raise Http404(
            _("The AIP package containing the requested METS cannot be found")
        )
    transfer_name = aip["_source"]["name"]
    return helpers.stream_mets_from_storage_service(
        transfer_name=transfer_name, sip_uuid=uuid
    )


def aip_pointer_file_download(request, uuid):
    redirect_url = storage_service.pointer_file_url(uuid)
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?"
    )


def send_thumbnail(request, fileuuid):
    # get AIP location to use to find root of AIP storage
    search_service = setup_search_service_from_conf(settings)
    aipfile = search_service.get_aipfile_data(fileuuid, fields=["AIPUUID"])
    sipuuid = aipfile["_source"]["AIPUUID"]

    thumbnail_path = os.path.join(
        settings.SHARED_DIRECTORY, "www", "thumbnails", sipuuid, fileuuid + ".jpg"
    )

    # send "blank" thumbnail if one exists:
    # Because thumbnails aren't kept in ElasticSearch they can be queried for,
    # during searches, from multiple dashboard servers.
    # Because ElasticSearch don't know if a thumbnail exists or not, this is
    # a way of not causing visual disruption if a thumbnail doesn't exist.
    if not os.path.exists(thumbnail_path):
        thumbnail_path = os.path.join(settings.BASE_PATH, "media/images/1x1-pixel.png")

    return helpers.send_file(request, thumbnail_path)


def aips_pending_deletion():
    aip_uuids = []
    try:
        aips = storage_service.get_file_info(
            status=archivematica.search.constants.STATUS_DELETE_REQUESTED
        )
    except Exception as e:
        # TODO this should be messages.warning, but we need 'request' here
        logger.warning(
            f"Error retrieving AIPs pending deletion: is the storage server running?  Error: {e}"
        )
    else:
        for aip in aips:
            aip_uuids.append(aip["uuid"])
    return aip_uuids


def elasticsearch_query_excluding_aips_pending_deletion(uuid_field_name):
    # add UUIDs of AIPs pending deletion, if any, to boolean query
    must_not_haves = []

    for aip_uuid in aips_pending_deletion():
        must_not_haves.append({"term": {uuid_field_name: aip_uuid}})

    if len(must_not_haves):
        query = {"query": {"bool": {"must_not": must_not_haves}}}
    else:
        query = {"query": {"match_all": {}}}

    return query


def aip_file_count(search_service):
    query = elasticsearch_query_excluding_aips_pending_deletion("AIPUUID")
    return search_service.count_aip_files(query)


def total_size_of_aips(search_service):
    query = elasticsearch_query_excluding_aips_pending_deletion("uuid")
    query["_source"] = "size"
    query["aggs"] = {"total": {"sum": {"field": "size"}}}
    results = search_service.search_aips(query, size=0)
    # TODO handle the return object
    total_size = results["aggregations"]["total"]["value"]
    # Size is stored in ES as MBs
    # Convert to bytes before using filesizeformat
    total_bytes = total_size * (1024 * 1024)
    total_size = filesizeformat(total_bytes)
    return total_size


def _document_json_response(document_id_modified, index):
    document_id = document_id_modified.replace("____", "-")
    search_service = setup_search_service_from_conf(settings)
    data = search_service.get_aipfile_by_document_id(document_id)
    pretty_json = json.dumps(data, sort_keys=True, indent=2)
    return HttpResponse(pretty_json, content_type="application/json")


def file_json(request, document_id_modified):
    return _document_json_response(
        document_id_modified, archivematica.search.constants.AIP_FILES_INDEX
    )


def view_aip(request, uuid):
    search_service = setup_search_service_from_conf(settings)
    try:
        es_aip_doc = search_service.get_aip_data(
            uuid, fields=["name", "size", "created", "status", "filePath", "encrypted"]
        )
    except AIPNotFoundError:
        raise Http404

    source = es_aip_doc["_source"]
    name = source.get("name")
    active_tab = None

    form_upload = forms.UploadMetadataOnlyAtomForm(prefix="upload")
    form_reingest = forms.ReingestAIPForm(prefix="reingest")
    form_delete = forms.DeleteAIPForm(prefix="delete", uuid=uuid)

    # Process metadata-only DIP upload form
    if request.POST and "submit-upload-form" in request.POST:
        form_upload = forms.UploadMetadataOnlyAtomForm(request.POST, prefix="upload")
        active_tab = "upload"
        if form_upload.is_valid():
            try:
                file_slug = upload_dip_metadata_to_atom(
                    name, uuid, form_upload.cleaned_data["slug"]
                )
            except AtomMetadataUploadError:
                messages.error(
                    request,
                    _(
                        "Metadata-only DIP upload failed, check the logs for more details"
                    ),
                )
                logger.error(
                    "Unexepected error during metadata-only DIP upload (UUID: %s)",
                    uuid,
                    exc_info=True,
                )
            else:
                messages.success(
                    request,
                    _(
                        "Metadata-only DIP upload has been completed successfully. New resource has slug: %(slug)s"
                    )
                    % {"slug": file_slug},
                )
            form_upload = forms.UploadMetadataOnlyAtomForm(
                prefix="upload"
            )  # Reset form

    # Process reingest form
    if request.POST and "submit-reingest-form" in request.POST:
        form_reingest = forms.ReingestAIPForm(request.POST, prefix="reingest")
        active_tab = "reingest"
        if form_reingest.is_valid():
            response = storage_service.request_reingest(
                uuid,
                form_reingest.cleaned_data["reingest_type"],
                form_reingest.cleaned_data["processing_config"],
            )
            error = response.get("error", True)
            message = response.get("message", "An unknown error occurred.")
            if error:
                messages.error(
                    request,
                    _("Error re-ingesting package: %(message)s") % {"message": message},
                )
            else:
                messages.success(request, message)
            return redirect("archival_storage:archival_storage_index")

    # Process delete form
    if request.POST and "submit-delete-form" in request.POST:
        form_delete = forms.DeleteAIPForm(request.POST, prefix="delete", uuid=uuid)
        active_tab = "delete"
        if form_delete.is_valid():
            response = storage_service.request_file_deletion(
                uuid,
                request.user.id,
                request.user.email,
                form_delete.cleaned_data["reason"],
            )
            messages.info(request, response["message"])
            search_service = setup_search_service_from_conf(settings)
            search_service.mark_aip_for_deletion(uuid)
            return redirect("archival_storage:archival_storage_index")

    context = {
        "uuid": uuid,
        "name": name,
        "created": source.get("created"),
        "status": AIP_STATUS_DESCRIPTIONS[
            source.get("status", archivematica.search.constants.STATUS_UPLOADED)
        ],
        "encrypted": source.get("encrypted", False),
        "size": "{:.2f} MB".format(source.get("size", 0)),
        "location_basename": os.path.basename(source.get("filePath")),
        "active_tab": active_tab,
        "forms": {
            "upload": form_upload,
            "reingest": form_reingest,
            "delete": form_delete,
        },
    }

    return render(request, "archival_storage/view.html", context)


def save_state(request, table):
    """Save DataTable state JSON object as string in DashboardSettings.

    :param request: Django request.
    :param table: Name of table to store state for.
    :return: JSON success confirmation
    """
    setting_name = f"{table}_datatable_state"
    state = json.dumps(request.body.decode("utf8"))
    helpers.set_setting(setting_name, state)
    return helpers.json_response({"success": True})


def load_state(request, table):
    """Retrieve DataTable state JSON object stored in DashboardSettings.

    :param request: Django request.
    :param table: Name of table to store state for.
    :return: JSON state
    """
    setting_name = f"{table}_datatable_state"
    state = helpers.get_setting(setting_name)
    if state:
        return HttpResponse(
            json.loads(state), content_type="application/json", status=200
        )
    return helpers.json_response(
        {"error": True, "message": "Setting not found"}, status_code=404
    )
