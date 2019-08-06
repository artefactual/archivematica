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

import logging

import dateutil.parser

logger = logging.getLogger("archivematica.dashboard.advanced_search")

OBJECT_FIELDS = ("mets", "transferMetadata")

OTHER_FIELDS = "transferMetadataOther"


def search_parameter_prep(request):
    queries = request.GET.getlist("query")
    ops = request.GET.getlist("op")
    fields = request.GET.getlist("field")
    types = request.GET.getlist("type")
    other_fields = request.GET.getlist("fieldName")

    # Prepend default op arg as first op can't be set manually, if there are no
    # entries, insert the first as "and" (a "must" clause). Otherwise copy
    # the existing first entry. This ensures that if the second clause is a
    # "should" the first entry will be too, etc.
    if len(ops) == 0:
        ops.insert(0, "and")
    else:
        ops.insert(0, ops[0])

    if len(queries) == 0:
        queries = ["*"]
        fields = [""]
    else:
        # Make sure each query has field/ops set
        for index, query in enumerate(queries):
            # A blank query makes ES error
            if queries[index] == "":
                queries[index] = "*"

            try:
                fields[index]
            except:
                fields.insert(index, "")

            try:
                ops[index]
            except:
                ops.insert(index, "and")

            if ops[index] == "":
                ops[index] = "and"

            try:
                types[index]
            except:
                types.insert(index, "")

        # For "other" fields, the actual title of the subfield is located in a
        # second array. Search for any such fields and replace the placeholder
        # value in the `fields` array with the full name.
        # In Elasticsearch, "." is used to search subdocuments; for example,
        # transferMetadata.Bagging-Date would be used to search for the value
        # of Bagging-Date in this nested object:
        # {
        #   "transferMetadata": {
        #     "Start-Date": 0000-00-00,
        #     "Bagging-Date": 0000-00-00
        #   }
        # }
        for index, field in enumerate(fields):
            if field == "transferMetadataOther":
                fields[index] = "transferMetadata." + other_fields[index]

    return queries, ops, fields, types


def extract_url_search_params_from_request(request):
    # Set pagination-related variables
    search_params = ""
    try:
        search_params = request.get_full_path().split("?")[1]
        end_of_search_params = search_params.index("&page")
        search_params = search_params[:end_of_search_params]
    except:
        pass
    return search_params


def assemble_query(queries, ops, fields, types, filters=[]):
    must_haves = []
    should_haves = []
    must_not_haves = []
    index = 0

    for query in queries:
        if queries[index] != "":
            clause = _query_clause(index, queries, ops, fields, types)
            if clause:
                if ops[index] == "not":
                    must_not_haves.append(clause)
                elif ops[index] == "and":
                    must_haves.append(clause)
                else:
                    should_haves.append(clause)

        index = index + 1

    # Return match all query if no clauses
    if len(must_haves + must_not_haves + should_haves + filters) == 0:
        return {"query": {"match_all": {}}}

    # TODO: Fix boolean query build:
    # Should clauses will only influence the weight of the results if
    # a must/must not/filter is present, but they will have no impact
    # on the returned results. When a should clause is parsed, it should
    # be added inside an extra boolean query with two should clauses,
    # one with the existing must and other with the new should, that
    # new boolean query has to be added as a the must in the final
    # boolean query. This should be done in orther instead of in the
    # end to reflect the input order in the boolean query.
    return {
        "query": {
            "bool": {
                "must": must_haves,
                "must_not": must_not_haves,
                "should": should_haves,
                "filter": filters,
            }
        }
    }


def _fix_object_fields(fields):
    """
    Adjusts field names for nested object fields.

    Elasticsearch is able to search through nested object fields, provided that
    the field name is specified appropriately in the query. Appending .* to the
    field name (for example, transferMetadata.*) causes Elasticsearch to
    consider any of the values within key/value pairs nested in the object
    being searched. Without doing this, Elasticsearch will attempt to match the
    value of transferMetadata itself, which will always fail since it's an
    object and not a string.
    """
    return [field + ".*" if field in OBJECT_FIELDS else field for field in fields]


def _parse_date_range(field):
    """
    Splits a range field into start and end values.

    Expects data in the following format:
        start:end
    """
    if ":" not in field:
        return ("", field)

    return field.split(":")[:2]


def _normalize_date(date):
    try:
        return dateutil.parser.parse(date).strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date received ({}); ignoring date query".format(date))


def _query_clause(index, queries, ops, fields, types):
    # Ignore empty queries
    if queries[index] in ("", "*"):
        return

    # Normalize fields
    if fields[index] == "":
        search_fields = []
    else:
        search_fields = _fix_object_fields([fields[index]])

    # Build query based on type
    query = None
    if types[index] == "term":
        query = {"multi_match": {"query": queries[index]}}
        if len(search_fields) > 0:
            query["multi_match"]["fields"] = search_fields
    elif types[index] == "string":
        query = {"query_string": {"query": queries[index]}}
        if len(search_fields) > 0:
            query["query_string"]["fields"] = search_fields
    elif types[index] == "range":
        start, end = _parse_date_range(queries[index])
        try:
            start = _normalize_date(start)
            end = _normalize_date(end)
        except ValueError as e:
            logger.info(str(e))
            return
        query = {"range": {fields[index]: {"gte": start, "lte": end}}}

    return query


def indexed_count(es_client, index, query=None):
    try:
        return es_client.count(index=index, body=query)["count"]
    except:
        return 0
