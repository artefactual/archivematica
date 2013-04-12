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

from django.shortcuts import render
from django.http import HttpResponse
from django.utils import simplejson
from components.archival_storage import forms
from django.conf import settings
from main import models
from components.filesystem_ajax.views import send_file
from components import advanced_search
from components import helpers
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
import httplib
import tempfile
import subprocess

AIPSTOREPATH = '/var/archivematica/sharedDirectory/www/AIPsStore'

def archival_storage(request):
    return archival_storage_list_display(request)

def archival_storage_page(request, page=None):
    return archival_storage_list_display(request, page)

def archival_storage_search(request):
    # deal with transfer mode
    file_mode = False
    checked_if_in_file_mode = ''
    if request.GET.get('mode', '') != '':
        file_mode = True
        checked_if_in_file_mode = 'checked'

    # get search parameters from request
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    # redirect if no search params have been set
    if not 'query' in request.GET:
        return helpers.redirect_with_get_params(
            'components.archival_storage.views.archival_storage_search',
            query='',
            field='',
            type=''
        )

    # get string of URL parameters that should be passed along when paging
    search_params = advanced_search.extract_url_search_params_from_request(request)

    # set paging variables
    if not file_mode:
        items_per_page = 10
    else:
        items_per_page = 20

    page = advanced_search.extract_page_number_from_url(request)

    start = page * items_per_page + 1

    # perform search
    conn = pyes.ES(elasticSearchFunctions.getElasticsearchServerHostAndPort())

    try:
        query=advanced_search.assemble_query(queries, ops, fields, types)

        # use all results to pull transfer facets if not in file mode
        if not file_mode:
            results = conn.search_raw(
                query=query,
                indices='aips',
                type='aipfile'
            )
        else:
            results = conn.search_raw(
                query=query,
                indices='aips',
                type='aipfile',
                start=start - 1,
                size=items_per_page
            )
    except:
        return HttpResponse('Error accessing index.')

    # take note of facet data
    file_extension_usage = results['facets']['fileExtension']['terms']
    aip_uuids            = results['facets']['AIPUUID']['terms']

    if not file_mode:
        number_of_results = len(aip_uuids)

        page_data = helpers.pager(aip_uuids, items_per_page, page + 1)
        aip_uuids = page_data['objects']
        archival_storage_search_augment_aip_results(conn, aip_uuids)
    else:
        number_of_results = results.hits.total
        results = archival_storage_search_augment_file_results(results)

    # set remaining paging variables
    end, previous_page, next_page = advanced_search.paging_related_values_for_template_use(
       items_per_page,
       page,
       start,
       number_of_results
    )

    # make sure results is set
    try:
        if results:
            pass
    except:
        results = False

    form = forms.StorageSearchForm(initial={'query': queries[0]})
    return render(request, 'archival_storage/archival_storage_search.html', locals())

def archival_storage_search_augment_aip_results(conn, aips):
    for aip_uuid in aips:
        documents = conn.search_raw(query=pyes.FieldQuery(pyes.FieldParameter('uuid', aip_uuid.term)))
        if len(documents['hits']['hits']) > 0:
            aip_uuid.name = documents['hits']['hits'][0]['_source']['name']
        else:
            aip_uuid.name = '(data missing)' 

def archival_storage_search_augment_file_results(raw_results):
    modifiedResults = []

    for item in raw_results.hits.hits:
        clone = item._source.copy()

        # try to find AIP details in database
        try:
            # get AIP data from ElasticSearch
            aip = elasticSearchFunctions.connect_and_get_aip_data(clone['AIPUUID'])

            # augment result data
            clone['sipname'] = aip.name
            clone['fileuuid'] = clone['FILEUUID']
            clone['href'] = aip.filePath.replace(AIPSTOREPATH + '/', "AIPsStore/")

        except:
            aip = None
            clone['sipname'] = False

        clone['filename'] = os.path.basename(clone['filePath'])
        clone['document_id'] = item['_id']
        clone['document_id_no_hyphens'] = item['_id'].replace('-', '____')

        modifiedResults.append(clone)

    return modifiedResults

def archival_storage_aip_download(request, uuid):
    aip = elasticSearchFunctions.connect_and_get_aip_data(uuid)
    return send_file(request, aip.filePath)

def archival_storage_aip_file_download(request, uuid):
    # get file basename
    file          = models.File.objects.get(uuid=uuid)
    file_basename = os.path.basename(file.currentlocation)

    # get file's AIP's properties
    sipuuid      = helpers.get_file_sip_uuid(uuid)
    aip          = elasticSearchFunctions.connect_and_get_aip_data(sipuuid)
    aip_filepath = aip.filePath

    # create temp dir to extract to
    temp_dir = tempfile.mkdtemp()

    # work out path components
    aip_archive_filename = os.path.basename(aip_filepath)
    subdir = os.path.splitext(aip_archive_filename)[0]
    path_to_file_within_aip_data_dir \
      = os.path.dirname(file.originallocation.replace('%transferDirectory%', ''))

    file_relative_path = os.path.join(
      subdir,
      'data',
      path_to_file_within_aip_data_dir,
      file_basename
    )

    #return HttpResponse('7za e -o' + temp_dir + ' ' + aip_filepath + ' ' + file_relative_path)

    # extract file from AIP
    command_data = [
        '7za',
        'e',
        '-o' + temp_dir,
        aip_filepath,
        file_relative_path
    ]

    subprocess.call(command_data)

    # send extracted file
    extracted_file_path = os.path.join(temp_dir, file_basename)
    return send_file(request, extracted_file_path)

def archival_storage_send_thumbnail(request, fileuuid):
    # get AIP location to use to find root of AIP storage
    sipuuid = helpers.get_file_sip_uuid(fileuuid)
    aip = elasticSearchFunctions.connect_and_get_aip_data(sipuuid)
    aip_filepath = aip.filePath

    # strip path to AIP from root of AIP storage
    for index in range(1, 10):
        aip_filepath = os.path.dirname(aip_filepath)

    # derive thumbnail path
    thumbnail_path = os.path.join(
        aip_filepath,
        'thumbnails',
        sipuuid,
        fileuuid + '.jpg'
    )

    # send "blank" thumbnail if one exists:
    # Because thumbnails aren't kept in ElasticSearch they can be queried for,
    # during searches, from multiple dashboard servers.
    # Because ElasticSearch don't know if a thumbnail exists or not, this is
    # a way of not causing visual disruption if a thumbnail doesn't exist.
    if not os.path.exists(thumbnail_path):
        thumbnail_path = os.path.join(settings.BASE_PATH, 'media/images/1x1-pixel.png')

    return send_file(request, thumbnail_path)

def archival_storage_list_display(request, current_page_number=None):
    form = forms.StorageSearchForm()

    total_size = 0

    # get ElasticSearch stats
    aip_indexed_file_count = advanced_search.indexed_count('aips')

    # get AIPs
    conn = elasticSearchFunctions.connect_and_create_index('aips')
    aipResults = conn.search(pyes.StringQuery('*'), doc_types=['aip'])
    aips = []

    #if aipResults._total != None:
    if len(aipResults) > 0:
        for aip in aipResults:
            aips.append(aip)

    # handle pagination
    page = helpers.pager(aips, 10, current_page_number)

    sips = []
    for aip in page['objects']:
        sip = {}
        sip['href'] = aip.filePath.replace(AIPSTOREPATH + '/', "AIPsStore/")
        sip['name'] = aip.name
        sip['uuid'] = aip.uuid

        #sip['date'] = str(aip.date)[0:19].replace('T', ' ')
        sip['date'] = aip.created

        try:
            size = float(aip.size)
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
    conn = httplib.HTTPConnection(elasticSearchFunctions.getElasticsearchServerHostAndPort())
    conn.request("GET", "/aips/aipfile/" + document_id)
    response = conn.getresponse()
    data = response.read()
    pretty_json = simplejson.dumps(simplejson.loads(data), sort_keys=True, indent=2)
    return HttpResponse(pretty_json, content_type='application/json')
