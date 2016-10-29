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

import logging
import requests

from django.conf import settings as django_settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template import RequestContext

import elasticSearchFunctions
import storageService as storage_service

# This project, alphabetical by import source
from components import advanced_search
from components import decorators
from components import helpers

logger = logging.getLogger('archivematica.dashboard')


def check_and_remove_deleted_transfers(es_client):
    """
    Check the storage service to see if transfers marked in ES as 'pending deletion' have been deleted yet. If so,
    remove the transfer and its files from ES. This is a bit of a kludge (that we do elsewhere e.g. in the storage tab),
    but it appears necessary as the storage service doesn't talk directly to ES.

    :return: None
    """
    query = {
        'query': {
            'bool': {
                'must': {
                    'match': {
                        'pending_deletion': True
                    }
                }
            }
        }
    }

    deletion_pending_results = es_client.search(
        body=query,
        index='transfers',
        doc_type='transfer',
        fields='uuid,status'
    )

    for hit in deletion_pending_results['hits']['hits']:
        transfer_uuid = hit['fields']['uuid'][0]

        api_results = storage_service.get_file_info(uuid=transfer_uuid)
        try:
            status = api_results[0]['status']
        except IndexError:
            logger.info('Transfer not found in storage service: {}'.format(transfer_uuid))
            continue

        if status == 'DELETED':
            elasticSearchFunctions.remove_backlog_transfer_files(es_client, transfer_uuid)
            elasticSearchFunctions.remove_backlog_transfer(es_client, transfer_uuid)


def execute(request):
    """
    Remove any deleted transfers from ES and render main backlog page.

    :param request: The Django request object
    :return: The main backlog page rendered
    """
    es_client = elasticSearchFunctions.get_client()
    check_and_remove_deleted_transfers(es_client)
    return render(request, 'backlog/backlog.html', locals())


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
        ('name', 'uuid', 'file_count', 'ingest_date', None),     # Transfers are being displayed
        ('filename', 'sipuuid', None)                            # Transfer files are being displayed
    )

    if index < 0 or index >= len(table_columns[file_mode]):
        logger.warning('Backlog column index specified is invalid for sorting, got %s', index)
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

    file_mode = request.GET.get('file_mode') == 'true'
    page_size = int(request.GET.get('iDisplayLength', 10))
    start = int(request.GET.get('iDisplayStart', 0))

    order_by = get_es_property_from_column_index(int(request.GET.get('iSortCol_0', 0)), file_mode)
    sort_direction = request.GET.get('sSortDir_0', 'asc')

    es_client = elasticSearchFunctions.get_client()

    if 'query' not in request.GET:
        queries, ops, fields, types = (['*'], ['or'], [''], ['term'])

    query = advanced_search.assemble_query(
        es_client, queries, ops, fields, types, search_index='transfers',
        doc_type='transferfile', filters={'term': {'status': 'backlog'}}
    )

    try:
        if file_mode:
            doc_type = 'transferfile'
            source = 'filename,sipuuid,relative_path'
        else:  # Transfer mode
            # Query to transfers/transferfile, but only fetch & aggregrate transfer UUIDs
            # Based on transfer UUIDs, query to transfers/transfer
            query['aggs'] = {'transfer_uuid': {'terms': {'field': 'sipuuid'}}}
            hits = es_client.search(
                index='transfers',
                doc_type='transferfile',
                body=query,
                size=0,  # Don't return results, only aggregation
            )
            uuids = [x['key'] for x in hits['aggregations']['transfer_uuid']['buckets']]

            query['query'] = {
                'terms': {
                    'uuid': uuids,
                },
            }
            doc_type = 'transfer'
            source = 'name,uuid,file_count,ingest_date'

        hit_count = es_client.search(index='transfers', doc_type=doc_type, body=query, search_type='count')['hits']['total']
        hits = es_client.search(
            index='transfers',
            doc_type=doc_type,
            body=query,
            from_=start,
            size=page_size,
            sort=order_by + ':' + sort_direction if order_by else '',
            _source=source,
        )

    except Exception:
        err_desc = 'Error accessing transfers index'
        logger.exception(err_desc)
        return HttpResponse(err_desc)

    results = [x['_source'] for x in hits['hits']['hits']]

    return helpers.json_response({
        'iTotalRecords': hit_count,
        'iTotalDisplayRecords': hit_count,
        'sEcho': int(request.GET.get('sEcho', 0)),  # It was recommended we convert sEcho to int to prevent XSS
        'aaData': results,
    })


def delete_context(request, uuid):
    """
    Provide contextual information to the deletion request page.

    :param request: The Django request object
    :param uuid: The UUID of the package requested for deletion.
    :return: The request context
    """
    prompt = 'Delete package?'
    cancel_url = reverse('components.backlog.views.execute')
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})


@decorators.confirm_required('delete_request.html', delete_context)
def delete(request, uuid):
    """
    Request deletion of a package from a backlog transfer

    :param request: The Django request object
    :param uuid: The UUID of the package requested for deletion.
    :return: Redirects the user back to the backlog page
    """
    try:
        reason_for_deletion = request.POST.get('reason_for_deletion', '')
        response = storage_service.request_file_deletion(
            uuid,
            request.user.id,
            request.user.email,
            reason_for_deletion
        )

        messages.info(request, response['message'])
        es_client = elasticSearchFunctions.get_client()
        elasticSearchFunctions.mark_backlog_deletion_requested(es_client, uuid)

    except requests.exceptions.ConnectionError:
        error_message = 'Unable to connect to storage server. Please contact your administrator.'
        messages.warning(request, error_message)
    except requests.exceptions.RequestException:
        raise Http404

    return redirect('backlog_index')


def download(request, uuid):
    """
    Download a package from a requested backlog transfer.

    :param request: The Django request object
    :param uuid: UUID for the transfer we're downloading the package from
    :return: Respond with a TAR'd version of the requested package
    """
    return helpers.stream_file_from_storage_service(storage_service.download_file_url(uuid))
