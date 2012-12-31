# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import simplejson
from components.archival_storage import forms
from main import models
from components.filesystem_ajax.views import send_file
from components import helpers
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
import httplib

AIPSTOREPATH = '/var/archivematica/sharedDirectory/www/AIPsStore'

def archival_storage(request):
    return archival_storage_sip_display(request)

def archival_storage_page(request, page=None):
    return archival_storage_sip_display(request, page)

def archival_storage_search(request):
    queries, ops, fields, types = archival_storage_search_parameter_prep(request)

    # set pagination-related variables
    search_params = ''
    try:
        search_params = request.get_full_path().split('?')[1]
        end_of_search_params = search_params.index('&page')
        search_params = search_params[:end_of_search_params]
    except:
        pass

    items_per_page = 20

    page = request.GET.get('page', 0)
    if page == '':
        page = 0
    page = int(page)

    start = page * items_per_page + 1

    conn = pyes.ES('127.0.0.1:9200')

    try:
        results = conn.search_raw(
            query=archival_storage_search_assemble_query(queries, ops, fields, types),
            indices='aips',
            type='aip',
            start=start - 1,
            size=items_per_page
        )
    except:
        return HttpResponse('Error accessing index.')

    file_extension_usage = results['facets']['fileExtension']['terms']
    number_of_results = results.hits.total
    results = archival_storage_search_augment_results(results)

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

    # make sure results is set
    try:
        if results:
            pass
    except:
        results = False

    form = forms.StorageSearchForm(initial={'query': queries[0]})
    return render(request, 'archival_storage/archival_storage_search.html', locals())

def archival_storage_search_parameter_prep(request):
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
                #fields[index] = ''

            try:
                ops[index]
            except:
                ops.insert(index, 'or')
                #ops[index] = ''

            try:
                types[index]
            except:
                types.insert(index, '')

            index = index + 1

    return queries, ops, fields, types

def archival_storage_search_assemble_query(queries, ops, fields, types):
    must_haves     = []
    should_haves   = []
    must_not_haves = []
    index          = 0

    for query in queries:
        if queries[index] != '':
            clause = archival_storage_search_query_clause(index, queries, ops, fields, types)
            if clause:
                if ops[index] == 'not':
                    must_not_haves.append(clause)
                elif ops[index] == 'and':
                    must_haves.append(clause)
                else:
                    should_haves.append(clause)

        index = index + 1

    q = pyes.BoolQuery(must=must_haves, should=should_haves, must_not=must_not_haves).search()
    q.facet.add_term_facet('fileExtension')

    return q

def archival_storage_search_query_clause(index, queries, ops, fields, types):
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
            return pyes.TermQuery(term_field, queries[index])
    else:
        return pyes.StringQuery(queries[index], search_fields=search_fields)

def archival_storage_search_augment_results(raw_results):
    modifiedResults = []

    for item in raw_results.hits.hits:
        clone = item._source.copy()

        # try to find AIP details in database
        try:
            aip = models.AIP.objects.get(sipuuid=clone['AIPUUID'])
            clone['sipname'] = aip.sipname
            clone['href']    = aip.filepath.replace(AIPSTOREPATH + '/', "AIPsStore/")
        except:
            aip = None
            clone['sipname'] = False

        clone['filename'] = os.path.basename(clone['filePath'])
        clone['document_id'] = item['_id']
        clone['document_id_no_hyphens'] = item['_id'].replace('-', '____')

        modifiedResults.append(clone)

    return modifiedResults

def archival_storage_indexed_count(index):
    aip_indexed_file_count = 0
    try:
        conn = pyes.ES('127.0.0.1:9200')
        count_data = conn.count(indices=index)
        aip_indexed_file_count = count_data.count
    except:
        pass
    return aip_indexed_file_count

def archival_storage_sip_download(request, uuid):
    aip = models.AIP.objects.get(sipuuid=uuid)
    return send_file(request, aip.filepath)

def archival_storage_sip_display(request, current_page_number=None):
    form = forms.StorageSearchForm()

    total_size = 0

    # get ElasticSearch stats
    aip_indexed_file_count = archival_storage_indexed_count('aips')

    # get AIPs from DB
    aips = models.AIP.objects.all()

    # handle pagination
    page = helpers.pager(aips, 10, current_page_number)

    sips = []
    for aip in page['objects']:
        sip = {}
        sip['href'] = aip.filepath.replace(AIPSTOREPATH + '/', "AIPsStore/")
        sip['name'] = aip.sipname
        sip['uuid'] = aip.sipuuid

        sip['date'] = aip.sipdate

        try:
            size = os.path.getsize(aip.filepath) / float(1024) / float(1024)
            total_size = total_size + size
            sip['size'] = '{0:.2f} MB'.format(size)
        except:
            sip['size'] = 'Removed'

        sips.append(sip)

    order_by = request.GET.get('order_by', 'name');
    sort_by  = request.GET.get('sort_by', 'up');

    def sort_aips(sip):
        value = 0
        if 'name' == order_by:
            value = sip['name'].lower()
        else:
            value = sip[order_by]
        return value
    sips = sorted(sips, key = sort_aips)

    if sort_by == 'down':
        sips.reverse()

    total_size = '{0:.2f}'.format(total_size)

    return render(request, 'archival_storage/archival_storage.html', locals())

def archival_storage_file_json(request, document_id_modified):
    document_id = document_id_modified.replace('____', '-')
    conn = httplib.HTTPConnection("127.0.0.1:9200")
    conn.request("GET", "/aips/aip/" + document_id)
    response = conn.getresponse()
    data = response.read()
    pretty_json = simplejson.dumps(simplejson.loads(data), sort_keys=True, indent=2)
    return HttpResponse(pretty_json, content_type='application/json')
