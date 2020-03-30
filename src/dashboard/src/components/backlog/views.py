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

from django.conf import settings as django_settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _
import requests

from amclient import AMClient

from archivematicaFunctions import get_setting
import elasticSearchFunctions
import storageService as storage_service

from components import advanced_search, decorators, helpers

logger = logging.getLogger("archivematica.dashboard")


def check_and_remove_deleted_transfers(es_client):
    """
    Check the storage service to see if transfers marked in ES as 'pending deletion' have been deleted yet. If so,
    remove the transfer and its files from ES. This is a bit of a kludge (that we do elsewhere e.g. in the storage tab),
    but it appears necessary as the storage service doesn't talk directly to ES.

    :return: None
    """
    query = {"query": {"bool": {"must": {"match": {"pending_deletion": True}}}}}

    deletion_pending_results = es_client.search(
        body=query, index="transfers", _source="uuid,status"
    )

    for hit in deletion_pending_results["hits"]["hits"]:
        transfer_uuid = hit["_source"]["uuid"]

        api_results = storage_service.get_file_info(uuid=transfer_uuid)
        try:
            status = api_results[0]["status"]
        except IndexError:
            logger.info(
                "Transfer not found in storage service: {}".format(transfer_uuid)
            )
            continue

        if status == "DELETED":
            elasticSearchFunctions.remove_backlog_transfer_files(
                es_client, transfer_uuid
            )
            elasticSearchFunctions.remove_backlog_transfer(es_client, transfer_uuid)


def check_and_update_transfer_pending_deletion(uuid, pending_deletion):
    """Check Storage Service to see if transfer has pending deletion and update ES if so.

    :param uuid: Transfer UUID.
    :param pending_deletion: Current pending_deletion value in transfers ES index.
    :return: None
    """
    api_results = AMClient(
        ss_api_key=get_setting("storage_service_apikey", ""),
        ss_user_name=get_setting("storage_service_user", ""),
        ss_url=get_setting("storage_service_url", "").rstrip("/"),
        package_uuid=uuid,
    ).get_package_details()
    if api_results in (1, 2, 3):
        logger.warning(
            "Package {} not found in Storage Service. AMClient error code: {}".format(
                uuid, api_results
            )
        )
        return

    transfer_status = api_results.get("status")

    if transfer_status is not None and transfer_status == "DEL_REQ":
        if pending_deletion is False:
            es_client = elasticSearchFunctions.get_client()
            elasticSearchFunctions.mark_backlog_deletion_requested(es_client, uuid)


def execute(request):
    """
    Remove any deleted transfers from ES and render main backlog page.

    :param request: The Django request object
    :return: The main backlog page rendered
    """
    if "transfers" in django_settings.SEARCH_ENABLED:
        es_client = elasticSearchFunctions.get_client()
        check_and_remove_deleted_transfers(es_client)
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

    es_client = elasticSearchFunctions.get_client()

    if "query" not in request.GET:
        queries, ops, fields, types = (["*"], ["or"], [""], ["term"])

    query = advanced_search.assemble_query(
        queries, ops, fields, types, filters=[{"term": {"status": "backlog"}}]
    )

    try:
        if file_mode:
            index = "transferfiles"
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
                index="transferfiles",
                body=query,
                size=0,  # Don't return results, only aggregation
            )
            uuids = [x["key"] for x in hits["aggregations"]["transfer_uuid"]["buckets"]]

            # Recreate query to search over transfers
            query = {"query": {"terms": {"uuid": uuids}}}
            index = "transfers"
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

    results = [x["_source"] for x in hits["hits"]["hits"]]

    for result in results:
        # Format size
        size = result.get("size")
        if size is not None:
            result["size"] = filesizeformat(size)

        if not file_mode:
            pending_deletion = result.get("pending_deletion")
            check_and_update_transfer_pending_deletion(result["uuid"], pending_deletion)

    return helpers.json_response(
        {
            "iTotalRecords": hit_count,
            "iTotalDisplayRecords": hit_count,
            "sEcho": int(
                request.GET.get("sEcho", 0)
            ),  # It was recommended we convert sEcho to int to prevent XSS
            "aaData": results,
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
    cancel_url = reverse("components.backlog.views.execute")
    return RequestContext(
        request, {"action": "Delete", "prompt": prompt, "cancel_url": cancel_url}
    )


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
        es_client = elasticSearchFunctions.get_client()
        elasticSearchFunctions.mark_backlog_deletion_requested(es_client, uuid)

    except requests.exceptions.ConnectionError:
        messages.warning(
            request,
            _(
                "Unable to connect to storage server. Please contact your administrator."
            ),
        )
    except requests.exceptions.RequestException:
        raise Http404

    return redirect("backlog_index")


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
    state = json.dumps(request.body)
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
