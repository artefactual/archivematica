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

from django.shortcuts import render
import elasticSearchFunctions

# This project, alphabetical by import source
from components import advanced_search
from components import decorators
from components import helpers

logger = logging.getLogger('archivematica.dashboard')


def execute(request):
    return render(request, 'backlog/backlog.html', locals())


@decorators.elasticsearch_required()
def search(request):
    # get search parameters from request
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)
    logger.debug('Backlog queries: %s, Ops: %s, Fields: %s, Types: %s', queries, ops, fields, types)

    file_mode = request.GET.get('filemode', False)

    conn = elasticSearchFunctions.connect_and_create_index('transfers')

    # get string of URL parameters that should be passed along when paging
    #search_params = advanced_search.extract_url_search_params_from_request(request)
    #current_page_number = int(request.GET.get('page', 1))

    results = None

    if 'query' not in request.GET:
        queries, ops, fields, types = ('*', 'or', '', '')

    query = advanced_search.assemble_query(queries, ops, fields, types, search_index='transfers',
                                           doc_type='transferfile', filters={'term': {'status': 'backlog'}})
    try:
        # use all results to pull transfer facets if not in file mode
        # pulling only one field (we don't need field data as we augment
        # the results using separate queries)
        if not file_mode:
            # Searching for AIPs still actually searches type 'aipfile', and
            # returns the UUID of the AIP the files are a part of.  To search
            # for an attribute of an AIP, the aipfile must index that
            # information about their AIP in
            # elasticSearchFunctions.index_mets_file_metadata
            # Because we're searching aips/aipfile and not aips/aip,
            # cannot using LazyPagedSequence
            results = conn.search(
                body=query,
                index='transfers',
                doc_type='transfer',
                #fields='AIPUUID,sipName',
                #sort='sipName:desc',
            )
        else:
            # To reduce amount of data fetched from ES, use LazyPagedSequence
            def es_pager(page, page_size):
                """
                Fetch one page of normalized aipfile entries from Elasticsearch.

                :param page: 1-indexed page to fetch
                :param page_size: Number of entries on a page
                :return: List of dicts for each entry with additional information
                """
                start = (page - 1) * page_size
                results = conn.search(
                    body=query,
                    index='aips',
                    doc_type='aipfile',
                    from_=start,
                    size=page_size,
                    fields='AIPUUID,filePath,FILEUUID',
                    sort='sipName:desc',
                )
                return search_augment_file_results(results)
            count = conn.count(index='aips', doc_type='aipfile', body={'query': query['query']})['count']
            results = LazyPagedSequence(es_pager, items_per_page, count)

    except:
        logger.exception('Error accessing index.')
        return HttpResponse('Error accessing index.')

    if file_mode:
        return helpers.json_response(results)
    else:
        transfers = elasticSearchFunctions.augment_raw_search_results(results)
        return helpers.json_response(transfers)

