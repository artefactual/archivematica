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
from django.http import HttpResponse

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
    """
    A JSON end point that returns results for various backlog transfers and their files.
    :param request:
    :return:
    """
    # get search parameters from request
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)
    logger.debug('Backlog queries: %s, Ops: %s, Fields: %s, Types: %s', queries, ops, fields, types)

    file_mode = True if request.GET.get('file_mode') == 'true' else False
    page_size = int(request.GET.get('iDisplayLength', 10))
    start = int(request.GET.get('iDisplayStart', 0))

    f = open('/tmp/lol', 'a')
    print >> f, 'File mode: %r | page size: %d | start: %d' % (file_mode, page_size, start)
    print >> f, repr(request.GET)

    conn = elasticSearchFunctions.connect_and_create_index('transfers')

    if 'query' not in request.GET:
        queries, ops, fields, types = (['*'], ['or'], [''], ['term'])

    print >> f, 'Queries: %r fields: %r types: %r ops: %r' % (queries, fields, types, ops)
    query = advanced_search.assemble_query(queries, ops, fields, types, search_index='transfers',
                                           doc_type='transferfile', filters={'term': {'status': 'backlog'}})
    try:
        doc_type = 'transferfile' if file_mode else 'transfer'

        hit_count = conn.search(index='transfers', doc_type=doc_type, body=query, search_type='count')['hits']['total']
        hits = conn.search(index='transfers', doc_type=doc_type, body=query, from_=start, size=page_size)

    except Exception as e:
        logger.exception('Error accessing index: {}'.format(e))
        return HttpResponse('Error accessing index.')

    r = {
        'iTotalRecords': hit_count,
        'iTotalDisplayRecords': hit_count,
        'sEcho': int(request.GET.get('sEcho', 0)),  # It was recommended we convert sEcho to int to prevent XSS
        'aaData': elasticSearchFunctions.augment_raw_search_results(hits)
    }

    print >> f, 'Replying: %r' % r

    return helpers.json_response(r)
