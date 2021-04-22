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
from __future__ import absolute_import

from collections import OrderedDict
import csv
from datetime import datetime
import json
import logging
import os
import uuid

from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import make_aware, get_current_timezone
from django.utils.translation import ugettext as _
from elasticsearch import ElasticsearchException
from pandas.io.json import json_normalize

from archivematicaFunctions import setup_amclient, AMCLIENT_ERROR_CODES
from components import advanced_search, helpers
from components.archival_storage import forms
from components.archival_storage.atom import (
    upload_dip_metadata_to_atom,
    AtomMetadataUploadError,
)
import databaseFunctions
import elasticSearchFunctions as es
import storageService as storage_service

logger = logging.getLogger("archivematica.dashboard")

AIPSTOREPATH = "/var/archivematica/sharedDirectory/www/AIPsStore"

AIP_STATUS_DESCRIPTIONS = {
    es.STATUS_UPLOADED: _("Stored"),
    es.STATUS_DELETE_REQUESTED: _("Deletion requested"),
}

DIRECTORY_PERMISSIONS = 0o770
FILE_PERMISSIONS = 0o660

CSV_MIMETYPE = "text/csv"
CSV_FILE_NAME = "archival-storage-report.csv"


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
            "Package {} not found in Storage Service. AMClient error code: {}".format(
                uuid, api_results
            )
        )
        return keep_in_results

    aip_status = api_results.get("status")

    if not aip_status:
        logger.warning(
            "Status for package {} could not be retrived from Storage Service."
        )
        return keep_in_results

    if (
        aip_status == es.STATUS_DELETE_REQUESTED
        and es_status != es.STATUS_DELETE_REQUESTED
    ):
        es_client = es.get_client()
        es.mark_aip_deletion_requested(es_client, uuid)
    elif aip_status == es.STATUS_UPLOADED and es_status != es.STATUS_UPLOADED:
        es_client = es.get_client()
        es.revert_aip_deletion_request(es_client, uuid)
    elif aip_status == es.STATUS_DELETED:
        keep_in_results = False
        es_client = es.get_client()
        es.delete_aip(es_client, uuid)
        es.delete_aip_files(es_client, uuid)

    return keep_in_results


def execute(request):
    """Remove any deleted AIPs from ES index and render main archival storage page.

    :param request: Django request object.
    :return: The main archival storage page rendered.
    """
    if es.AIPS_INDEX in settings.SEARCH_ENABLED:
        es_client = es.get_client()

        total_size = total_size_of_aips(es_client)
        aip_indexed_file_count = aip_file_count(es_client)

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


def _ordered_dict_from_es_fields():
    """Ordered dict from es fields

    Archivematica code currently uses a mix of snake case, camel case,
    and other inconsistent variants of both for its Elasticsearch
    field names. Here we create a mapping to enable their output to
    something nice to read. We can also use this function to guarantee
    the field output ordering and make sure that the fields output are
    translatable.
    """
    column_lookup = OrderedDict()
    column_lookup[es.ES_FIELD_NAME] = _("Name")
    column_lookup[es.ES_FIELD_UUID] = _("UUID")
    column_lookup[es.ES_FIELD_AICID] = _("AICID")
    column_lookup[es.ES_FIELD_AICCOUNT] = _("Count AIPs in AIC")
    column_lookup[es.ES_FIELD_SIZE] = _("Size")
    column_lookup[es.ES_FIELD_FILECOUNT] = _("File count")
    column_lookup[es.ES_FIELD_ACCESSION_IDS] = _("Accession IDs")
    column_lookup[es.ES_FIELD_CREATED] = _("Created date (UTC)")
    column_lookup[es.ES_FIELD_STATUS] = _("Status")
    column_lookup["type"] = _("Type")
    column_lookup[es.ES_FIELD_ENCRYPTED] = _("Encrypted")
    column_lookup[es.ES_FIELD_LOCATION] = _("Location")
    return column_lookup


def _order_columns_for_file_download(data_frame):
    data_frame = data_frame.reindex(columns=list(_ordered_dict_from_es_fields().keys()))
    return data_frame


def _normalize_accession_ids_for_file_download(data_frame):
    """Normalize accession ids for file download

    It's rare that accession IDs will ever be an array proper. That
    being said if they ever are then arrays suit some data types better
    than others. For CSV, for example, we will use this function to
    return a list so the values
    can be parsed from a single-cell.
    """
    ACCESSION_IDS_FIELD = es.ES_FIELD_ACCESSION_IDS
    FIELD_SEPARATOR = "; "
    for i, cell in enumerate(data_frame[ACCESSION_IDS_FIELD]):
        normalized_value = FIELD_SEPARATOR.join(cell)
        data_frame.at[i, ACCESSION_IDS_FIELD] = normalized_value
    return data_frame


def _localize_date_output_for_file_download(data_frame):
    CREATED_FIELD = es.ES_FIELD_CREATED
    data_frame[CREATED_FIELD] = data_frame[CREATED_FIELD].apply(str)
    for i, cell in enumerate(data_frame[CREATED_FIELD]):
        normalized_value = make_aware(
            datetime.fromtimestamp(float(cell)), timezone=get_current_timezone()
        )
        data_frame.at[i, CREATED_FIELD] = normalized_value
    return data_frame


def _normalize_column_names_for_file_download(data_frame):
    """Normalize data columns for file download

    Prettify and order the column headers by removing 'variable' naming
    conventions and enable translation of column headers using
    predictable values.
    """
    data_frame.columns = [
        _ordered_dict_from_es_fields().get(column_name, column_name)
        for column_name in data_frame.columns
    ]
    return data_frame


def search_as_csv(data_frame, file_name=CSV_FILE_NAME):
    ENCODING = "utf-8"
    CONTENT_DISPOSITION_HDR = "Content-Disposition"
    MIME_HDR = "mimetype"
    CONTENT_DISPOSITION = 'attachment; filename="{}"'.format(file_name)
    response = StreamingHttpResponse(
        data_frame.to_csv(
            encoding=ENCODING, quoting=csv.QUOTE_ALL, index=False, chunksize=1024
        ),
        content_type=CSV_MIMETYPE,
    )
    response[CONTENT_DISPOSITION_HDR] = CONTENT_DISPOSITION
    response[MIME_HDR] = "{}; charset={}".format(CSV_MIMETYPE, ENCODING)
    return response


def search_as_file(es_results, file_name, mime_type):
    data_frame = json_normalize(es_results)
    # Normalize our data so that the report is consistent and useful.
    data_frame = _order_columns_for_file_download(data_frame)
    data_frame = _normalize_accession_ids_for_file_download(data_frame)
    data_frame = _localize_date_output_for_file_download(data_frame)
    # Lastly now we've done all the work we need to do on the columns
    # we can fix-up the names for user-friendly output.
    data_frame = _normalize_column_names_for_file_download(data_frame)
    if mime_type != CSV_MIMETYPE:
        logger.debug(
            "Client requested '%s' for the archival storage report but only CSV is supported at this time"
        )
    return search_as_csv(data_frame, file_name)


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
    file_name = request.GET.get(FILE_NAME, "")

    # Configure page-size requirements for the search.
    DEFAULT_PAGE_SIZE = 10
    page_size = None
    if request.GET.get(RETURN_ALL, "").lower() == "true":
        page_size = es.MAX_QUERY_SIZE
    if page_size is None:
        page_size = int(request.GET.get("iDisplayLength", DEFAULT_PAGE_SIZE))

    # Get search parameters from the request.
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    if "query" not in request.GET:
        queries, ops, fields, types = (["*"], ["or"], [""], ["term"])
    query = advanced_search.assemble_query(queries, ops, fields, types)
    file_mode = request.GET.get("file_mode") == "true"

    # Configure other aspects of the search including starting page and sort
    # order.
    start = int(request.GET.get("iDisplayStart", 0))
    order_by = get_es_property_from_column_index(
        int(request.GET.get("iSortCol_0", 0)), file_mode
    )
    sort_direction = request.GET.get("sSortDir_0", "asc")

    es_client = es.get_client()
    try:
        if file_mode:
            index = es.AIP_FILES_INDEX
            source = "filePath,FILEUUID,AIPUUID,accessionid,status"
        else:
            # Fetch all unique AIP UUIDs in the returned set of files.
            # ES query will limit to 10 aggregation results by default;
            # add size parameter in terms to override.
            # TODO: Use composite aggregation when it gets out of beta.
            query["aggs"] = {
                "aip_uuids": {"terms": {"field": "AIPUUID", "size": "10000"}}
            }
            # Don't return results, just the aggregation.
            query["size"] = 0
            # Searching for AIPs still actually searches type 'aipfile', and
            # returns the UUID of the AIP the files are a part of. To search
            # for an attribute of an AIP, the aipfile must index that
            # information about their AIP.
            results = es_client.search(body=query, index=es.AIP_FILES_INDEX)
            # Given these AIP UUIDs, now fetch the actual information we want
            # from AIPs/AIP.
            buckets = results["aggregations"]["aip_uuids"]["buckets"]
            uuids = [bucket["key"] for bucket in buckets]
            uuid_file_counts = {
                bucket["key"]: bucket["doc_count"] for bucket in buckets
            }
            query = {"query": {"terms": {"uuid": uuids}}}
            index = es.AIPS_INDEX
            source = "name,uuid,size,accessionids,created,status,encrypted,AICID,isPartOf,countAIPsinAIC,location"

        results = es_client.search(
            index=index,
            body=query,
            from_=start,
            size=page_size,
            sort=order_by + ":" + sort_direction if order_by else "",
            _source=source,
        )

        if file_mode:
            augmented_results = search_augment_file_results(es_client, results)
        else:
            augmented_results = search_augment_aip_results(results, uuid_file_counts)

        if request_file and not file_mode:
            return search_as_file(
                augmented_results, file_name=file_name, mime_type=file_mime
            )

        hit_count = results["hits"]["total"]

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

    except ElasticsearchException:
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
            "status": AIP_STATUS_DESCRIPTIONS[fields.get("status", es.STATUS_UPLOADED)],
            "encrypted": fields.get("encrypted", False),
            "accessionids": fields.get("accessionids", []),
            "location": fields.get("location", ""),
        }
        size = fields.get("size")
        if size is not None:
            bytecount = size * (1024 * 1024)
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


def search_augment_file_results(es_client, raw_results):
    """Augment file results.

    :param es_client: Elasticsearch client.
    :param raw_results: Raw results returned from ES.

    :return: Augmented and formatted results.
    """
    modifiedResults = []

    for item in raw_results["hits"]["hits"]:
        if "_source" not in item:
            continue

        clone = item["_source"].copy()

        try:
            aip = es.get_aip_data(
                es_client,
                clone["AIPUUID"],
                fields="uuid,name,filePath,size,origin,created,encrypted",
            )

            clone["sipname"] = aip["_source"]["name"]
            clone["fileuuid"] = clone["FILEUUID"]
            clone["href"] = aip["_source"]["filePath"].replace(
                AIPSTOREPATH + "/", "AIPsStore/"
            )

        except ElasticsearchException:
            aip = None
            clone["sipname"] = False

        clone["status"] = AIP_STATUS_DESCRIPTIONS[
            clone.get("status", es.STATUS_UPLOADED)
        ]
        clone["filename"] = os.path.basename(clone["filePath"])
        clone["document_id"] = item["_id"]
        clone["document_id_no_hyphens"] = item["_id"].replace("-", "____")

        modifiedResults.append(clone)

    return modifiedResults


def create_aic(request):
    """Create an AIC from POSTed list of AIP UUIDs.

    :param request: Django request object.
    :return: Redirect to appropriate view.
    """
    uuids = request.GET.get("uuids")
    if not uuids:
        messages.error(request, "Unable to create AIC: No AIPs selected")
        return redirect("archival_storage:archival_storage_index")

    # Make a list of UUIDs from from comma-separated string in request.
    aip_uuids = uuids.split(",")
    logger.info("AIC AIP UUIDs: {}".format(aip_uuids))

    # Use the AIP UUIDs to fetch names, which are used to produce files below.
    query = {"query": {"terms": {"uuid": aip_uuids}}}
    es_client = es.get_client()
    results = es_client.search(
        body=query, index=es.AIPS_INDEX, _source="uuid,name", size=es.MAX_QUERY_SIZE
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
        logger.exception("Error creating AIC: {}".format(e))
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
    es_client = es.get_client()

    # get AIP file properties
    aipfile = es.get_aipfile_data(es_client, uuid, fields="filePath,FILEUUID,AIPUUID")

    # get file's AIP's properties
    sipuuid = aipfile["_source"]["AIPUUID"]
    aip = es.get_aip_data(
        es_client, sipuuid, fields="uuid,name,filePath,size,origin,created"
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
    es_client = es.get_client()
    try:
        aip = es.get_aip_data(es_client, uuid, fields="name")
    except IndexError:
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
    es_client = es.get_client()
    aipfile = es.get_aipfile_data(es_client, fileuuid, fields="AIPUUID")
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
        aips = storage_service.get_file_info(status=es.STATUS_DELETE_REQUESTED)
    except Exception as e:
        # TODO this should be messages.warning, but we need 'request' here
        logger.warning(
            "Error retrieving AIPs pending deletion: is the storage server running?  Error: {}".format(
                e
            )
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


def aip_file_count(es_client):
    query = elasticsearch_query_excluding_aips_pending_deletion("AIPUUID")
    return advanced_search.indexed_count(es_client, es.AIP_FILES_INDEX, query)


def total_size_of_aips(es_client):
    query = elasticsearch_query_excluding_aips_pending_deletion("uuid")
    query["_source"] = "size"
    query["aggs"] = {"total": {"sum": {"field": "size"}}}
    results = es_client.search(body=query, index=es.AIPS_INDEX)
    # TODO handle the return object
    total_size = results["aggregations"]["total"]["value"]
    # Size is stored in ES as MBs
    # Convert to bytes before using filesizeformat
    total_bytes = total_size * (1024 * 1024)
    total_size = filesizeformat(total_bytes)
    return total_size


def _document_json_response(document_id_modified, index):
    document_id = document_id_modified.replace("____", "-")
    es_client = es.get_client()
    data = es_client.get(index=index, doc_type=es.DOC_TYPE, id=document_id)
    pretty_json = json.dumps(data, sort_keys=True, indent=2)
    return HttpResponse(pretty_json, content_type="application/json")


def file_json(request, document_id_modified):
    return _document_json_response(document_id_modified, es.AIP_FILES_INDEX)


def view_aip(request, uuid):
    es_client = es.get_client()
    try:
        es_aip_doc = es.get_aip_data(
            es_client, uuid, fields="name,size,created,status,filePath,encrypted"
        )
    except IndexError:
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
            es_client = es.get_client()
            es.mark_aip_deletion_requested(es_client, uuid)
            return redirect("archival_storage:archival_storage_index")

    context = {
        "uuid": uuid,
        "name": name,
        "created": source.get("created"),
        "status": AIP_STATUS_DESCRIPTIONS[source.get("status", es.STATUS_UPLOADED)],
        "encrypted": source.get("encrypted", False),
        "size": "{0:.2f} MB".format(source.get("size", 0)),
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
    setting_name = "{}_datatable_state".format(table)
    state = json.dumps(request.body.decode("utf8"))
    helpers.set_setting(setting_name, state)
    return helpers.json_response({"success": True})


def load_state(request, table):
    """Retrieve DataTable state JSON object stored in DashboardSettings.

    :param request: Django request.
    :param table: Name of table to store state for.
    :return: JSON state
    """
    setting_name = "{}_datatable_state".format(table)
    state = helpers.get_setting(setting_name)
    if state:
        return HttpResponse(
            json.loads(state), content_type="application/json", status=200
        )
    return helpers.json_response(
        {"error": True, "message": "Setting not found"}, status_code=404
    )
