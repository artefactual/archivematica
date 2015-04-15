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
import logging
import sys

import dateutil.parser
from elasticsearch import Elasticsearch

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions

logger = logging.getLogger("archivematica.dashboard.advanced_search")

OBJECT_FIELDS = (
    "mets",
    "transferMetadata",
)

OTHER_FIELDS = (
    "transferMetadataOther"
)

def search_parameter_prep(request):
    queries = request.GET.getlist('query')
    ops     = request.GET.getlist('op')
    fields  = request.GET.getlist('field')
    types   = request.GET.getlist('type')
    other_fields = request.GET.getlist('fieldName')

    # prepend default op arg as first op can't be set manually
    ops.insert(0, 'or')

    if len(queries) == 0:
        queries = ['*']
        fields  = ['']
    else:
        # make sure each query has field/ops set
        for index, query in enumerate(queries):
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

        # For "other" fields, the actual title of the subfield is located in a second array;
        # search for any such fields and replace the placeholder value in the `fields` array
        # with the full name.
        # In Elasticsearch, "." is used to search subdocuments; for example,
        # transferMetadata.Bagging-Date would be used to search for the value of Bagging-Date
        # in this nested object:
        # {
        #   "transferMetadata": {
        #     "Start-Date": 0000-00-00,
        #     "Bagging-Date": 0000-00-00
        #   }
        # }
        for index, field in enumerate(fields):
            if field == "transferMetadataOther":
                fields[index] = 'transferMetadata.' + other_fields[index]

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

def _fix_object_fields(fields):
    """
    Adjusts field names for nested object fields.

    Elasticsearch is able to search through nested object fields, provided that the field name is specified appropriately in the query.
    Appending .* to the field name (for example, transferMetadata.*) causes Elasticsearch to consider any of the values within key/value pairs nested in the object being searched.
    Without doing this, Elasticsearch will attempt to match the value of transferMetadata itself, which will always fail since it's an object and not a string.
    """
    return [field + '.*' if field in OBJECT_FIELDS else field for field in fields]

def _parse_date_range(field):
    """
    Splits a range field into start and end values.

    Expects data in the following format:
        start:end
    """
    if ':' not in field:
        return ('', field)

    return field.split(':')[:2]

def _normalize_date(date):
    try:
        return dateutil.parser.parse(date).strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date received ({}); ignoring date query".format(date))

def query_clause(index, queries, ops, fields, types):
    if fields[index] == '':
        search_fields = []
    else:
        search_fields = _fix_object_fields([fields[index]])

    if types[index] == 'term':
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
    elif types[index] == 'string':
        return {'query_string': {'query': queries[index], 'fields': search_fields}}
    elif types[index] == 'range':
        start, end = _parse_date_range(queries[index])
        try:
            start = _normalize_date(start)
            end = _normalize_date(end)
        except ValueError as e:
            logger.info(str(e))
            return
        return {'range': {fields[index]: {'gte': start, 'lte': end}}}

def indexed_count(index, types=None, query=None):
    if types is not None:
        types = ','.join(types)
    try:
        conn = Elasticsearch(hosts=elasticSearchFunctions.getElasticsearchServerHostAndPort())
        return conn.count(index=index, doc_type=types, body=query)['count']
    except:
        return 0
