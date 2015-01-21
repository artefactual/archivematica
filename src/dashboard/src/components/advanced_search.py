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

from django.http import HttpResponse
import sys

from elasticsearch import Elasticsearch

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions

def search_parameter_prep(request):
    queries = request.GET.getlist('query')
    ops     = request.GET.getlist('op')
    fields  = request.GET.getlist('field')
    types   = request.GET.getlist('type')

    # prepend default op arg as first op can't be set manually
    ops.insert(0, 'or')

    if len(queries) == 0:
        queries = ['*']
        fields  = ['']
    else:
        index = 0

        # make sure each query has field/ops set
        for query in queries:
            # a blank query makes ES error
            if queries[index] == '':
                queries[index] = '*'

            try:
                fields[index]
            except:
                fields.insert(index, '')

            try:
                ops[index]
            except:
                ops.insert(index, 'or')

            try:
                types[index]
            except:
                types.insert(index, '')

            index = index + 1

    return queries, ops, fields, types

# these are used in templates to prevent query params
def extract_url_search_params_from_request(request):
    # set pagination-related variables
    search_params = ''
    try:
        search_params = request.get_full_path().split('?')[1]
        end_of_search_params = search_params.index('&page')
        search_params = search_params[:end_of_search_params]
    except:
        pass
    return search_params

def extract_page_number_from_url(request):
    page = request.GET.get('page', 0)
    if page == '':
        page = 0
    return int(page)

def paging_related_values_for_template_use(items_per_page, page, start, number_of_results):
    # limit end by total hits
    end = start + items_per_page - 1
    if end > number_of_results:
        end = number_of_results

    # determine the previous page, if any
    previous_page = False
    if page > 0:
        previous_page = page - 1

    # determine the next page, if any
    next_page = False
    if (items_per_page * (page + 1)) < number_of_results:
        next_page = page + 1

    return end, previous_page, next_page

def assemble_query(queries, ops, fields, types, **kwargs):
    must_haves     = kwargs.get('must_haves', [])
    should_haves   = []
    must_not_haves = []
    index          = 0

    for query in queries:
        if queries[index] != '':
            clause = query_clause(index, queries, ops, fields, types)
            if clause:
                if ops[index] == 'not':
                    must_not_haves.append(clause)
                elif ops[index] == 'and':
                    must_haves.append(clause)
                else:
                    should_haves.append(clause)

        index = index + 1

    return {
        "query": {
            "bool": {
                "must": must_haves,
                "must_not": must_not_haves,
                "should": should_haves,
            }
        },
        "facets": {
            "fileExtension": {
                "terms": {
                    "field": "fileExtension"
                }
            },
            "sipuuid": {
                "terms": {
                    "field": "sipuuid",
                    "size": 1000000000
                }
            },
            "AIPUUID": {
                "terms": {
                    "field": "AIPUUID",
                    "size": 1000000000
                }
            }
        }
    }

def query_clause(index, queries, ops, fields, types):
    if fields[index] == '':
        search_fields = []
    else:
        search_fields = [fields[index]]

    if (types[index] == 'term'):
        # a blank term should be ignored because it prevents any results: you
        # can never find a blank term
        #
        # TODO: add condition to deal with a query with no clauses because all have
        #       been ignored
        if (queries[index] == ''):
            return
        else:
            if (fields[index] != ''):
                 term_field = fields[index]
            else:
                term_field = '_all'
            return {'term': {term_field: queries[index]}}
    else:
        return {'query_string': {'query': queries[index], 'fields': search_fields}}

def indexed_count(index, types=None, query=None):
    if types is not None:
        types = ','.join(types)
    try:
        conn = Elasticsearch(hosts=elasticSearchFunctions.getElasticsearchServerHostAndPort())
        return conn.count(index=index, doc_type=types, body=query)['count']
    except:
        return 0
