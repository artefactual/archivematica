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
from main import filesystem
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
    query = request.GET.get('query', '')

    if query == '':
        query = '*'

    # set pagination-related variables
    items_per_page = 20

    page = request.GET.get('page', 0)
    if page == '':
        page = 0
    page = int(page)

    start = page * items_per_page + 1

    conn = pyes.ES('127.0.0.1:9200')

    # do fulltext search
    q = pyes.StringQuery(query)

    try:
        results = conn.search_raw(query=q, indices='aips', type='aip', start=start - 1, size=items_per_page)
    except:
        return HttpResponse('Error accessing index.')

    # augment result data
    modifiedResults = []

    for item in results.hits.hits:
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

    number_of_results = results.hits.total

    # use augmented result data
    results = modifiedResults

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

    form = forms.StorageSearchForm(initial={'query': query})
    return render(request, 'archival_storage/archival_storage_search.html', locals())

def archival_storage_indexed_count(index):
    aip_indexed_file_count = 0
    try:
        conn = pyes.ES('127.0.0.1:9200')
        count_data = conn.count(indices=index)
        aip_indexed_file_count = count_data.count
    except:
        pass
    return aip_indexed_file_count

def archival_storage_sip_download(request, path):
    full_path = os.path.join(os.path.dirname(AIPSTOREPATH), path)
    return filesystem.send_file(request, full_path)

def archival_storage_sip_display(request, current_page_number=None):
    form = forms.StorageSearchForm()

    total_size = 0

    # get ElasticSearch stats
    aip_indexed_file_count = archival_storage_indexed_count('aips')

    # get AIPs from DB
    aips = models.AIP.objects.all()

    # handle pagination
    p                   = Paginator(aips, 20)
    current_page_number = 1 if current_page_number == None else int(current_page_number)
    page                = p.page(current_page_number)
    has_next            = page.has_next()
    next_page           = current_page_number + 1
    has_previous        = page.has_previous()
    previous_page       = current_page_number - 1
    has_other_pages     = page.has_other_pages()

    sips = []
    for aip in page.object_list:
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
