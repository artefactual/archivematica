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

from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _
import requests

from archivematicaFunctions import setup_amclient, AMCLIENT_ERROR_CODES
import elasticSearchFunctions as es
import storageService as storage_service

from components import advanced_search, decorators, helpers

logger = logging.getLogger("archivematica.dashboard")


def sync_es_transfer_status_with_storage_service(uuid, pending_deletion):
    """Update transfer's status in ES indices to match Storage Service.

    This is a bit of a kludge that is made necessary by the fact that
    the Storage Service does not update ElasticSearch directly when
    a package's status has changed.

    Updates to ES are visible in Backlog after running a new
    search or refreshing the page.

    :param uuid: Transfer UUID.
    :param pending_deletion: Current pending_deletion value in ES.

    :returns: Boolean indicating whether transfer should be kept in
    search results (i.e. has not been deleted from Storage Service).
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

    transfer_status = api_results.get("status")

    if not transfer_status:
        logger.warning(
            "Status for package {} could not be retrived from Storage Service."
        )
        return keep_in_results

    if transfer_status == es.STATUS_DELETE_REQUESTED and pending_deletion is False:
        es_client = es.get_client()
        es.mark_backlog_deletion_requested(es_client, uuid)
    elif transfer_status == es.STATUS_UPLOADED and pending_deletion is True:
        es_client = es.get_client()
        es.revert_backlog_deletion_request(es_client, uuid)
    elif transfer_status == es.STATUS_DELETED:
        keep_in_results = False
        es_client = es.get_client()
        es.remove_backlog_transfer_files(es_client, uuid)
        es.remove_backlog_transfer(es_client, uuid)

    return keep_in_results


def execute(request):
    """
    Render main backlog page.

    :param request: The Django request object
    :return: The main backlog page rendered
    """
    return render(request, "backlog/backlog.html", locals())


def get_es_property_from_column_index(index, file_mode):
    """
    When the user clicks a column header in the data table, we'll receive info in the ajax request
    telling us which column # we're supposed to sort across in our query. This function will translate
    the column index to the corresponding property name we'll tell ES to sort on.

    :param index: The column index that the data table says we're sorting on
    :param file_mode: Whether we're looking at transfers or transfer files
    :return: The ES document property name corresponding to the column index in the data table.
    """
    table_columns = (
        (
            "name.raw",
            "uuid",
            "size",
            "file_count",
            "accessionid",
            "ingest_date",
            "pending_deletion",
            None,
        ),  # Transfers are being displayed
        (
            "filename.raw",
            "sipuuid",
            "accessionid",
            "pending_deletion",
            None,
        ),  # Transfer files are being displayed
    )

    if index < 0 or index >= len(table_columns[file_mode]):
        logger.warning(
            "Backlog column index specified is invalid for sorting, got %s", index
        )
        index = 0

    return table_columns[file_mode][index]


def search(request):
    """
    A JSON end point that returns results for various backlog transfers and their files.

    :param request: The Django request object
    :return: A JSON object including required metadata for the datatable and the backlog search results.
    """
    # get search parameters from request
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    file_mode = request.GET.get("file_mode") == "true"
    page_size = int(request.GET.get("iDisplayLength", 10))
    start = int(request.GET.get("iDisplayStart", 0))

    order_by = get_es_property_from_column_index(
        int(request.GET.get("iSortCol_0", 0)), file_mode
    )
    sort_direction = request.GET.get("sSortDir_0", "asc")

    es_client = es.get_client()

    if "query" not in request.GET:
        queries, ops, fields, types = (["*"], ["or"], [""], ["term"])

    query = advanced_search.assemble_query(
        queries, ops, fields, types, filters=[{"term": {"status": "backlog"}}]
    )

    try:
        if file_mode:
            index = es.TRANSFER_FILES_INDEX
            source = "filename,sipuuid,relative_path,accessionid,pending_deletion"
        else:
            # Transfer mode:
            # Query to transferfile, but only fetch & aggregrate transfer UUIDs.
            # Based on transfer UUIDs, query to transfers.
            # ES query will limit to 10 aggregation results by default,
            # add size parameter in terms to override.
            # TODO: Use composite aggregation when it gets out of beta.
            query["aggs"] = {
                "transfer_uuid": {"terms": {"field": "sipuuid", "size": "10000"}}
            }
            hits = es_client.search(
                index=es.TRANSFER_FILES_INDEX,
                body=query,
                size=0,  # Don't return results, only aggregation
            )
            uuids = [x["key"] for x in hits["aggregations"]["transfer_uuid"]["buckets"]]

            # Recreate query to search over transfers
            query = {"query": {"terms": {"uuid": uuids}}}
            index = es.TRANSFERS_INDEX
            source = (
                "name,uuid,file_count,ingest_date,accessionid,size,pending_deletion"
            )

        hits = es_client.search(
            index=index,
            body=query,
            from_=start,
            size=page_size,
            sort=order_by + ":" + sort_direction if order_by else "",
            _source=source,
        )
        hit_count = hits["hits"]["total"]

    except Exception:
        err_desc = "Error accessing transfers index"
        logger.exception(err_desc)
        return HttpResponse(err_desc)

    search_results = []

    es_results = [x["_source"] for x in hits["hits"]["hits"]]

    for result in es_results:
        # Format size
        size = result.get("size")
        if size is not None:
            result["size"] = filesizeformat(size)

        if file_mode:
            # We only check status against the Storage Service for
            # transfers, so include all files in search results.
            search_results.append(result)
        else:
            pending_deletion = result.get("pending_deletion")
            keep_in_results = sync_es_transfer_status_with_storage_service(
                result["uuid"], pending_deletion
            )
            # Only return details for transfers that haven't been
            # deleted from the Storage Service in the search results.
            if keep_in_results:
                search_results.append(result)

    return helpers.json_response(
        {
            "iTotalRecords": hit_count,
            "iTotalDisplayRecords": hit_count,
            "sEcho": int(
                request.GET.get("sEcho", 0)
            ),  # It was recommended we convert sEcho to int to prevent XSS
            "aaData": search_results,
        }
    )


def delete_context(request, uuid):
    """
    Provide contextual information to the deletion request page.

    :param request: The Django request object
    :param uuid: The UUID of the package requested for deletion.
    :return: The request context
    """
    prompt = "Delete package?"
    cancel_url = reverse("backlog:backlog_index")
    return {"action": "Delete", "prompt": prompt, "cancel_url": cancel_url}


@decorators.confirm_required("delete_request.html", delete_context)
def delete(request, uuid):
    """
    Request deletion of a package from a backlog transfer

    :param request: The Django request object
    :param uuid: The UUID of the package requested for deletion.
    :return: Redirects the user back to the backlog page
    """
    try:
        reason_for_deletion = request.POST.get("reason_for_deletion", "")
        response = storage_service.request_file_deletion(
            uuid, request.user.id, request.user.email, reason_for_deletion
        )

        messages.info(request, response["message"])
        es_client = es.get_client()
        es.mark_backlog_deletion_requested(es_client, uuid)

    except requests.exceptions.ConnectionError:
        messages.warning(
            request,
            _(
                "Unable to connect to storage server. Please contact your administrator."
            ),
        )
    except requests.exceptions.RequestException:
        raise Http404

    return redirect("backlog:backlog_index")


def download(request, uuid):
    """
    Download a package from a requested backlog transfer.

    :param request: The Django request object
    :param uuid: UUID for the transfer we're downloading the package from
    :return: Respond with a TAR'd version of the requested package
    """
    return helpers.stream_file_from_storage_service(
        storage_service.download_file_url(uuid)
    )


def save_state(request, table):
    """
    Save DataTable state JSON object as string in DashboardSettings.

    :param table: Name of table to store state for.
    :return: JSON success confirmation
    """
    setting_name = "{}_datatable_state".format(table)
    state = json.dumps(request.body.decode("utf8"))
    helpers.set_setting(setting_name, state)
    return helpers.json_response({"success": True})


def load_state(request, table):
    """
    Retrieve DataTable state JSON object stored in DashboardSettings.

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
