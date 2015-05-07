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
    # if there are no entries, insert the first as "or" (e.g. a "should" clause);
    # otherwise copy the existing first entry
    # this ensures that if the second clause is a "must," the first entry will be too, etc.
    if len(ops) == 0:
        ops.insert(0, 'or')
    else:
        ops.insert(0, ops[0])

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

def assemble_query(queries, ops, fields, types, search_index=None, doc_type=None, **kwargs):
    must_haves     = kwargs.get('must_haves', [])
    filters        = kwargs.get('filters', {})
    should_haves   = []
    must_not_haves = []
    index          = 0

    for query in queries:
        if queries[index] != '':
            clause = query_clause(index, queries, ops, fields, types, search_index=search_index, doc_type=doc_type)
            if clause:
                if ops[index] == 'not':
                    must_not_haves.append(clause)
                elif ops[index] == 'and':
                    must_haves.append(clause)
                else:
                    should_haves.append(clause)

        index = index + 1

    return {
        "filter": filters,
        "query": {
            "bool": {
                "must": must_haves,
                "must_not": must_not_haves,
                "should": should_haves,
            }
        },
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

def filter_search_fields(search_fields, index=None, doc_type=None):
    """
    Given search fields which search nested documents with wildcards (such as "transferMetadata.*"), returns a list of subfields filtered to contain only string-type fields.

    When searching all fields of nested documents of mixed types using query_string queries, query_string queries may fail because the way the query string is interpreted depends on the type of the field being searched.
    For example, given a nested document containing a string field and a date field, a query_string of "foo" would fail when Elasticsearch attempts to parse it as a date to match it against the date field.
    This function uses the actual current mapping, so it supports automatically-mapped fields.

    Sample input and output, given a nested document containing three fields, "Bagging-Date" (date), "Bag-Name" (string), and "Bag-Type" (string):
    ["transferMetadata.*"] #=> ["transferMetadata.Bag-Name", "transferMetadata.Bag-Type"]

    :param list search_fields: A list of strings representing nested object names.
    :param str index: The name of the search index, used to look up the mapping document.
        If not provided, the original search_fields is returned unmodified.
    :param str doc_type: The name of the document type within the search index, used to look up the mapping document.
        If not provided, the original search_fields is returned unmodified.
    """
    if index is None or doc_type is None:
        return search_fields

    new_fields = []
    for field in search_fields:
        # Not a wildcard nested document search, so just add to the list as-is
        if not field.endswith('.*'):
            new_fields.append(field)
            continue
        try:
            field_name = field.rsplit('.', 1)[0]
            conn = elasticSearchFunctions.connect_and_create_index(index)
            mapping = elasticSearchFunctions.get_type_mapping(conn, index, doc_type)
            subfields = mapping[doc_type]['properties'][field_name]['properties']
        except KeyError:
            # The requested field doesn't exist in the index, so don't worry about validating subfields
            new_fields.append(field)
        else:
            for subfield, field_properties in subfields.iteritems():
                if field_properties['type'] == 'string':
                    new_fields.append(field_name + '.' + subfield)

    return new_fields

def query_clause(index, queries, ops, fields, types, search_index=None, doc_type=None):
    if fields[index] == '':
        search_fields = []
    else:
        search_fields = filter_search_fields(_fix_object_fields([fields[index]]), index=search_index, doc_type=doc_type)

    if types[index] == 'term':
        # a blank term should be ignored because it prevents any results: you
        # can never find a blank term
        #
        # TODO: add condition to deal with a query with no clauses because all have
        #       been ignored
        if (queries[index] in ('', '*')):
            return
        else:
            if len(search_fields) == 0:
                search_fields = ['_all']
            return {'multi_match': {'query': queries[index], 'fields': search_fields}}
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
