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

import json
import logging
import os
import uuid

from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _
from elasticsearch import ElasticsearchException

from amclient import AMClient

from components import advanced_search, helpers
from components.archival_storage import forms
from components.archival_storage.atom import (
    upload_dip_metadata_to_atom,
    AtomMetadataUploadError,
)
import databaseFunctions
import elasticSearchFunctions
import storageService as storage_service

logger = logging.getLogger("archivematica.dashboard")

AIPSTOREPATH = "/var/archivematica/sharedDirectory/www/AIPsStore"

AIP_STATUS_DESCRIPTIONS = {"UPLOADED": _("Stored"), "DEL_REQ": _("Deletion requested")}


def check_and_remove_deleted_aips(es_client):
    """Remove AIP and files from ES index if Storage Service status is deleted.

    Check the storage service to see if transfers marked in ES as
    'pending deletion' have been deleted yet.

    :param es_client: Elasticsearch client
    :return: None
    """
    query = {"query": {"bool": {"must": {"match": {"status": "DEL_REQ"}}}}}

    deletion_pending_results = es_client.search(
        body=query, index="aips", _source="uuid,status"
    )

    for hit in deletion_pending_results["hits"]["hits"]:
        aip_uuid = hit["_source"]["uuid"]

        api_results = storage_service.get_file_info(uuid=aip_uuid)
        try:
            aip_status = api_results[0]["status"]
        except IndexError:
            logger.info("AIP not found in storage service: {}".format(aip_uuid))
            continue

        if aip_status == "DELETED":
            elasticSearchFunctions.delete_aip(es_client, aip_uuid)
            elasticSearchFunctions.delete_aip_files(es_client, aip_uuid)
        elif aip_status != "DEL_REQ":
            elasticSearchFunctions.mark_aip_stored(es_client, aip_uuid)


def check_and_update_aip_pending_deletion(uuid, es_status):
    """Check Storage Service to see if AIP has pending deletion and update ES if so.

    :param uuid: AIP UUID.
    :param pending_deletion: Current pending_deletion value in aips ES index.
    :return: None
    """
    api_results = AMClient(
        ss_api_key=helpers.get_setting("storage_service_apikey", ""),
        ss_user_name=helpers.get_setting("storage_service_user", ""),
        ss_url=helpers.get_setting("storage_service_url", "").rstrip("/"),
        package_uuid=uuid,
    ).get_package_details()

    AMCLIENT_ERROR_CODES = (1, 2, 3)
    if api_results in AMCLIENT_ERROR_CODES:
        logger.warning(
            "Package {} not found in storage service. AMClient error code: {}".format(
                uuid, api_results
            )
        )
        return

    aip_status = api_results.get("status")

    if aip_status is not None and aip_status == "DEL_REQ":
        if es_status != "DEL_REQ":
            es_client = elasticSearchFunctions.get_client()
            elasticSearchFunctions.mark_aip_deletion_requested(es_client, uuid)


def execute(request):
    """Remove any deleted AIPs from ES index and render main archival storage page.

    :param request: The Django request object
    :return: The main archival storage page rendered
    """
    if "aips" in settings.SEARCH_ENABLED:
        es_client = elasticSearchFunctions.get_client()
        check_and_remove_deleted_aips(es_client)

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


def search(request):
    """A JSON end point that returns results for AIPs and their files.

    :param request: The Django request object
    :return: A JSON object including required metadata for the datatable and the search results.
    """
    # Get search parameters from request
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    file_mode = request.GET.get("file_mode") == "true"
    page_size = int(request.GET.get("iDisplayLength", 10))
    start = int(request.GET.get("iDisplayStart", 0))

    order_by = get_es_property_from_column_index(
        int(request.GET.get("iSortCol_0", 0)), file_mode
    )
    sort_direction = request.GET.get("sSortDir_0", "asc")

    es_client = elasticSearchFunctions.get_client()

    if "query" not in request.GET:
        queries, ops, fields, types = (["*"], ["or"], [""], ["term"])

    query = advanced_search.assemble_query(queries, ops, fields, types)

    try:
        if file_mode:
            index = "aipfiles"
            source = "filePath,FILEUUID,AIPUUID,accessionid,status"
        else:
            # Fetch all unique AIP UUIDs in the returned set of files
            # ES query will limit to 10 aggregation results by default,
            # add size parameter in terms to override.
            # TODO: Use composite aggregation when it gets out of beta.
            query["aggs"] = {
                "aip_uuids": {"terms": {"field": "AIPUUID", "size": "10000"}}
            }
            # Don't return results, just the aggregation
            query["size"] = 0
            # Searching for AIPs still actually searches type 'aipfile', and
            # returns the UUID of the AIP the files are a part of.  To search
            # for an attribute of an AIP, the aipfile must index that
            # information about their AIP.
            results = es_client.search(body=query, index="aipfiles")
            # Given these AIP UUIDs, now fetch the actual information we want from aips/aip
            buckets = results["aggregations"]["aip_uuids"]["buckets"]
            uuids = [bucket["key"] for bucket in buckets]
            uuid_file_counts = {
                bucket["key"]: bucket["doc_count"] for bucket in buckets
            }
            query = {"query": {"terms": {"uuid": uuids}}}
            index = "aips"
            source = "name,uuid,size,accessionids,created,status,encrypted,AICID,isPartOf,countAIPsinAIC"

        results = es_client.search(
            index=index,
            body=query,
            from_=start,
            size=page_size,
            sort=order_by + ":" + sort_direction if order_by else "",
            _source=source,
        )
        hit_count = results["hits"]["total"]

        if file_mode:
            augmented_results = search_augment_file_results(es_client, results)
        else:
            augmented_results = search_augment_aip_results(results, uuid_file_counts)

        return helpers.json_response(
            {
                "iTotalRecords": hit_count,
                "iTotalDisplayRecords": hit_count,
                "sEcho": int(
                    request.GET.get("sEcho", 0)
                ),  # It was recommended we convert sEcho to int to prevent XSS
                "aaData": augmented_results,
            }
        )

    except ElasticsearchException:
        err_desc = "Error accessing AIPs index"
        logger.exception(err_desc)
        return HttpResponse(err_desc)


def search_augment_aip_results(raw_results, counts):
    """Augment AIP results and check and update ES status if AIP is pending deletion.

    We perform check_and_update_aip_pending_deletion routine here to avoid
    needing to iterate through all of the results a second time.

    :param raw_results: Raw results returned from ES
    :param counts: Count of file UUIDs associated with AIP

    :return: Augmented and formatted results
    """
    modified_results = []

    for item in raw_results["hits"]["hits"]:
        fields = item["_source"]
        new_item = {
            "name": fields.get("name"),
            "uuid": fields.get("uuid"),
            "file_count": counts[fields["uuid"]],
            "created": fields.get("created"),
            "isPartOf": fields.get("isPartOf"),
            "AICID": fields.get("AICID"),
            "countAIPsinAIC": fields.get("countAIPsinAIC", "(unknown)"),
            "status": AIP_STATUS_DESCRIPTIONS[fields.get("status", "UPLOADED")],
            "encrypted": fields.get("encrypted", False),
            "accessionids": fields.get("accessionids"),
        }
        size = fields.get("size")
        if size is not None:
            bytecount = size * (1024 * 1024)
            new_item["size"] = filesizeformat(bytecount)
        modified_results.append(new_item)

        aic_id = fields.get("AICID")
        if aic_id and "AIC#" in aic_id:
            new_item["type"] = "AIC"
        else:
            new_item["type"] = "AIP"

        status = fields.get("status")
        if status is not None:
            check_and_update_aip_pending_deletion(fields["uuid"], status)

    return modified_results


def search_augment_file_results(es_client, raw_results):
    """Augment AIP file results.

    :param es_client: Elasticsearch client
    :param raw_results: Raw results returned from ES

    :return: Augmented and formatted results
    """
    modifiedResults = []

    for item in raw_results["hits"]["hits"]:
        if "_source" not in item:
            continue

        clone = item["_source"].copy()

        # try to find AIP details in database
        try:
            # get AIP data from ElasticSearch
            aip = elasticSearchFunctions.get_aip_data(
                es_client,
                clone["AIPUUID"],
                fields="uuid,name,filePath,size,origin,created,encrypted",
            )

            # augment result data
            clone["sipname"] = aip["_source"]["name"]
            clone["fileuuid"] = clone["FILEUUID"]
            clone["href"] = aip["_source"]["filePath"].replace(
                AIPSTOREPATH + "/", "AIPsStore/"
            )

        except ElasticsearchException:
            aip = None
            clone["sipname"] = False

        clone["status"] = AIP_STATUS_DESCRIPTIONS[clone.get("status", "UPLOADED")]
        clone["filename"] = os.path.basename(clone["filePath"])
        clone["document_id"] = item["_id"]
        clone["document_id_no_hyphens"] = item["_id"].replace("-", "____")

        modifiedResults.append(clone)

    return modifiedResults


def create_aic(request):
    """Create AIC from POST-ed list of AIP UUIDs.

    :param request: Django request object.
    :return: Direct to ingest tab.
    """
    uuids = request.POST.get("uuids")
    if not uuids:
        messages.error(request, "Unable to create AIC: No AIPs selected")
        return redirect("archival_storage_index")

    # Make list from comma-separated string of UUIDs
    aip_uuids = uuids.split(",")
    logger.info("AIC AIP UUIDs: {}".format(aip_uuids))

    # Use AIP UUIDs to fetch their names, which is used to produce files below
    query = {"query": {"terms": {"uuid": aip_uuids}}}
    es_client = elasticSearchFunctions.get_client()
    results = es_client.search(
        body=query,
        index="aips",
        _source="uuid,name",
        size=elasticSearchFunctions.MAX_QUERY_SIZE,  # return all records
    )

    # Create files in staging directory with AIP information
    shared_dir = settings.SHARED_DIRECTORY
    staging_dir = os.path.join(shared_dir, "tmp")

    # Create SIP (AIC) directory in staging directory
    temp_uuid = str(uuid.uuid4())
    destination = os.path.join(staging_dir, temp_uuid)
    try:
        os.mkdir(destination)
        os.chmod(destination, 0o770)
    except os.error:
        messages.error(request, "Error creating AIC")
        logger.exception(
            "Error creating AIC: Error creating directory {}".format(destination)
        )
        return redirect("archival_storage_index")

    # Create SIP in DB
    mcp_destination = destination.replace(shared_dir, "%sharedPath%") + "/"
    databaseFunctions.createSIP(mcp_destination, UUID=temp_uuid, sip_type="AIC")

    # Create files with filename = AIP UUID, and contents = AIP name
    for aip in results["hits"]["hits"]:
        filepath = os.path.join(destination, aip["_source"]["uuid"])
        with open(filepath, "w") as f:
            os.chmod(filepath, 0o660)
            f.write(str(aip["_source"]["name"]))

    return redirect("components.ingest.views.aic_metadata_add", temp_uuid)


def aip_download(request, uuid):
    redirect_url = storage_service.download_file_url(uuid)
    return helpers.stream_file_from_storage_service(
        redirect_url, "Storage service returned {}; check logs?"
    )


def aip_file_download(request, uuid):
    es_client = elasticSearchFunctions.get_client()

    # get AIP file properties
    aipfile = elasticSearchFunctions.get_aipfile_data(
        es_client, uuid, fields="filePath,FILEUUID,AIPUUID"
    )

    # get file's AIP's properties
    sipuuid = aipfile["_source"]["AIPUUID"]
    aip = elasticSearchFunctions.get_aip_data(
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
    es_client = elasticSearchFunctions.get_client()
    try:
        aip = elasticSearchFunctions.get_aip_data(es_client, uuid, fields="name")
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
    es_client = elasticSearchFunctions.get_client()
    aipfile = elasticSearchFunctions.get_aipfile_data(
        es_client, fileuuid, fields="AIPUUID"
    )
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
        aips = storage_service.get_file_info(status="DEL_REQ")
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
    return advanced_search.indexed_count(es_client, "aipfiles", query)


def total_size_of_aips(es_client):
    query = elasticsearch_query_excluding_aips_pending_deletion("uuid")
    query["_source"] = "size"
    query["aggs"] = {"total": {"sum": {"field": "size"}}}
    results = es_client.search(body=query, index="aips")
    # TODO handle the return object
    total_size = results["aggregations"]["total"]["value"]
    # Size is stored in ES as MBs
    # Convert to bytes before using filesizeformat
    total_bytes = total_size * (1024 * 1024)
    total_size = filesizeformat(total_bytes)
    return total_size


def _document_json_response(document_id_modified, index):
    document_id = document_id_modified.replace("____", "-")
    es_client = elasticSearchFunctions.get_client()
    data = es_client.get(
        index=index, doc_type=elasticSearchFunctions.DOC_TYPE, id=document_id
    )
    pretty_json = json.dumps(data, sort_keys=True, indent=2)
    return HttpResponse(pretty_json, content_type="application/json")


def file_json(request, document_id_modified):
    return _document_json_response(document_id_modified, "aipfiles")


def view_aip(request, uuid):
    es_client = elasticSearchFunctions.get_client()
    try:
        es_aip_doc = elasticSearchFunctions.get_aip_data(
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
            return redirect("archival_storage_index")

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
            es_client = elasticSearchFunctions.get_client()
            elasticSearchFunctions.mark_aip_deletion_requested(es_client, uuid)
            return redirect("archival_storage_index")

    context = {
        "uuid": uuid,
        "name": name,
        "created": source.get("created"),
        "status": AIP_STATUS_DESCRIPTIONS[source.get("status", "UPLOADED")],
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
    state = json.dumps(request.body)
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
