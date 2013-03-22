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

from django.db.models import Max
from django.conf import settings as django_settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import connection
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson
from contrib.mcp.client import MCPClient
from contrib import utils
from main import forms
from main import models
from lxml import etree
from components.ingest.forms import DublinCoreMetadataForm
from components.ingest.views_NormalizationReport import getNormalizationReportQuery
from components import helpers
import calendar, ConfigParser
import cPickle
import components.decorators as decorators
from components import helpers
from components import advanced_search
import os, sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
from components.archival_storage.forms import StorageSearchForm
from components.filesystem_ajax.views import send_file

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def ingest_grid(request):
    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    uid = request.user.id
    return render(request, 'ingest/grid.html', locals())

def ingest_status(request, uuid=None):
    # Equivalent to: "SELECT SIPUUID, MAX(createdTime) AS latest FROM Jobs WHERE unitType='unitSIP' GROUP BY SIPUUID
    objects = models.Job.objects.filter(hidden=False, subjobof='').values('sipuuid').annotate(timestamp=Max('createdtime')).exclude(sipuuid__icontains = 'None').filter(unittype__exact = 'unitSIP')
    mcp_available = False
    try:
        client = MCPClient()
        mcp_status = etree.XML(client.list())
        mcp_available = True
    except Exception: pass
    def encoder(obj):
        items = []
        for item in obj:
            # Check if hidden (TODO: this method is slow)
            if models.SIP.objects.is_hidden(item['sipuuid']):
                continue
            jobs = helpers.get_jobs_by_sipuuid(item['sipuuid'])
            item['directory'] = utils.get_directory_name(jobs[0])
            item['timestamp'] = calendar.timegm(item['timestamp'].timetuple())
            item['uuid'] = item['sipuuid']
            item['id'] = item['sipuuid']
            del item['sipuuid']
            item['jobs'] = []
            for job in jobs:
                newJob = {}
                item['jobs'].append(newJob)

                # allow user to know name of file that has failed normalization
                if job.jobtype == 'Access normalization failed - copying' or job.jobtype == 'Preservation normalization failed - copying' or job.jobtype == 'thumbnail normalization failed - copying':
                    task = models.Task.objects.get(job=job)
                    newJob['filename'] = task.filename

                newJob['uuid'] = job.jobuuid
                newJob['type'] = job.jobtype
                newJob['microservicegroup'] = job.microservicegroup
                newJob['subjobof'] = job.subjobof
                newJob['currentstep'] = job.currentstep
                newJob['timestamp'] = '%d.%s' % (calendar.timegm(job.createdtime.timetuple()), str(job.createdtimedec).split('.')[-1])
                try: mcp_status
                except NameError: pass
                else:
                    xml_unit = mcp_status.xpath('choicesAvailableForUnit[UUID="%s"]' % job.jobuuid)
                    if xml_unit:
                        xml_unit_choices = xml_unit[0].findall('choices/choice')
                        choices = {}
                        for choice in xml_unit_choices:
                            choices[choice.find("chainAvailable").text] = choice.find("description").text
                        newJob['choices'] = choices
            items.append(item)
        return items
    response = {}
    response['objects'] = objects
    response['mcp'] = mcp_available
    return HttpResponse(simplejson.JSONEncoder(default=encoder).encode(response), mimetype='application/json')

def ingest_sip_metadata_type_id():
    return helpers.get_metadata_type_id_by_description('SIP')

@decorators.load_jobs # Adds jobs, name
def ingest_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    metadata = models.DublinCore.objects.filter(metadataappliestotype__exact=ingest_sip_metadata_type_id(), metadataappliestoidentifier__exact=uuid)

    return render(request, 'ingest/metadata_list.html', locals())

def ingest_metadata_edit(request, uuid, id=None):
    if id:
        dc = models.DublinCore.objects.get(pk=id)
    else:
        # Right now we only support linking metadata to the Ingest
        try:
            dc = models.DublinCore.objects.get_sip_metadata(uuid)
            return HttpResponseRedirect(reverse('components.ingest.views.ingest_metadata_edit', args=[uuid, dc.id]))
        except ObjectDoesNotExist:
            dc = models.DublinCore(metadataappliestotype=ingest_sip_metadata_type_id(), metadataappliestoidentifier=uuid)

    fields = ['title', 'creator', 'subject', 'description', 'publisher',
              'contributor', 'date', 'type', 'format', 'identifier',
              'source', 'relation', 'language', 'coverage', 'rights']

    if request.method == 'POST':
        form = DublinCoreMetadataForm(request.POST)
        if form.is_valid():
            for item in fields:
                setattr(dc, item, form.cleaned_data[item])
            dc.save()
            return HttpResponseRedirect(reverse('components.ingest.views.ingest_metadata_list', args=[uuid]))
    else:
        initial = {}
        for item in fields:
            initial[item] = getattr(dc, item)
        form = DublinCoreMetadataForm(initial=initial)
        jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
        name = utils.get_directory_name(jobs[0])

    return render(request, 'ingest/metadata_edit.html', locals())

def ingest_metadata_delete(request, uuid, id):
    try:
        models.DublinCore.objects.get(pk=id).delete()
        return HttpResponseRedirect(reverse('components.ingest.views.ingest_detail', args=[uuid]))
    except:
        raise Http404

def ingest_detail(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    is_waiting = jobs.filter(currentstep='Awaiting decision').count() > 0
    name = utils.get_directory_name(jobs[0])
    return render(request, 'ingest/detail.html', locals())

def ingest_microservices(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name(jobs[0])
    return render(request, 'ingest/microservices.html', locals())

def ingest_delete(request, uuid):
    try:
        sip = models.SIP.objects.get(uuid__exact=uuid)
        sip.hidden = True
        sip.save()
        response = simplejson.JSONEncoder().encode({ 'removed': True })
        return HttpResponse(response, mimetype='application/json')
    except:
        raise Http404

def ingest_upload(request, uuid):
    """
        The upload DIP is actually not executed here, but some data is storaged
        in the database (permalink, ...), used later by upload-qubit.py
        - GET = It could be used to obtain DIP size
        - POST = Create Accesses tuple with permalink
    """
    try:
        sip = models.SIP.objects.get(uuid__exact=uuid)
    except:
        raise Http404

    if request.method == 'POST':
        if 'target' in request.POST:
            try:
                access = models.Access.objects.get(sipuuid=uuid)
            except:
                access = models.Access(sipuuid=uuid)
            access.target = cPickle.dumps({
              "target": request.POST['target'],
              "intermediate": request.POST['intermediate'] == "true" })
            access.save()
            response = simplejson.JSONEncoder().encode({ 'ready': True })
            return HttpResponse(response, mimetype='application/json')
    elif request.method == 'GET':
        try:
            access = models.Access.objects.get(sipuuid=uuid)
            data = cPickle.loads(str(access.target))
        except:
            # pass
            raise Http404
        # Disabled, it could be very slow
        # job = models.Job.objects.get(jobtype='Upload DIP', sipuuid=uuid)
        # data['size'] = utils.get_directory_size(job.directory)
        response = simplejson.JSONEncoder().encode(data)
        return HttpResponse(response, mimetype='application/json')

    return HttpResponseBadRequest()

def ingest_normalization_report(request, uuid, current_page=None):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    job = jobs[0]
    sipname = utils.get_directory_name(job)

    query = getNormalizationReportQuery()
    cursor = connection.cursor()
    cursor.execute(query, ( uuid, uuid, uuid, uuid, uuid, uuid, uuid, uuid ))
    objects = helpers.dictfetchall(cursor)

    results_per_page = 10

    if current_page == None:
        current_page = 1

    page = helpers.pager(objects, results_per_page, current_page)
    hit_count = len(objects)

    return render(request, 'ingest/normalization_report.html', locals())

def ingest_browse_normalization(request, jobuuid):
    jobs = models.Job.objects.filter(jobuuid=jobuuid, subjobof='')
    job = jobs[0]
    title = 'Review normalization'
    name = utils.get_directory_name(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/approveNormalization'

    return render(request, 'ingest/aip_browse.html', locals())

def ingest_browse_aip(request, jobuuid):
    """
    jobs = models.Job.objects.filter(jobuuid=jobuuid)

    if jobs.count() == 0:
      raise Http404

    job = jobs[0]
    sipuuid = job.sipuuid

    sips = models.SIP.objects.filter(uuid=sipuuid)
    sip = sips[0]

    aipdirectory = sip.currentpath.replace(
      '%sharedPath%',
      '/var/archivematica/sharedDirectory/'
    )
    """
    jobs = models.Job.objects.filter(jobuuid=jobuuid, subjobof='')
    job = jobs[0]
    title = 'Review AIP'
    name = utils.get_directory_name(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/storeAIP'

    return render(request, 'ingest/aip_browse.html', locals())

def transfer_backlog(request):
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)
 
    if not 'query' in request.GET:
        return helpers.redirect_with_get_params('components.ingest.views.transfer_backlog', query='', field='', type='')

    # set pagination-related variables to use in template
    search_params = advanced_search.extract_url_search_params_from_request(request)

    items_per_page = 20

    page = advanced_search.extract_page_number_from_url(request)

    start = page * items_per_page + 1

    conn = pyes.ES(elasticSearchFunctions.getElasticsearchServerHostAndPort())

    try:
        results = conn.search_raw(
            query=advanced_search.assemble_query(queries, ops, fields, types),
            indices='transfers',
            type='transferfile',
            start=start - 1,
            size=items_per_page
        )
    except:
        return HttpResponse('Error accessing index.')

    file_extension_usage = results['facets']['fileExtension']['terms']
    number_of_results = results.hits.total
    results = transfer_backlog_augment_search_results(results)

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

    form = StorageSearchForm(initial={'query': queries[0]})
    return render(request, 'ingest/backlog/search.html', locals())

def transfer_backlog_augment_search_results(raw_results):
    modifiedResults = []

    for item in raw_results.hits.hits:
        clone = item._source.copy()

        clone['awaiting_creation'] = transfer_awaiting_sip_creation(clone['sipuuid'])

        clone['document_id'] = item['_id']
        clone['document_id_no_hyphens'] = item['_id'].replace('-', '____')

        modifiedResults.append(clone)

    return modifiedResults

def transfer_awaiting_sip_creation(uuid):
    try:
        job = models.Job.objects.filter(
            sipuuid=uuid,
            microservicegroup='Create SIP from Transfer',
            currentstep='Awaiting decision'
        )[0]
        return True
    except:
        return False

def process_transfer(request, uuid):
    response = {}

    if request.user.id:
        client = MCPClient()
        try:
            job = models.Job.objects.filter(
                sipuuid=uuid,
                microservicegroup='Create SIP from Transfer',
                currentstep='Awaiting decision'
            )[0]
            chain = models.MicroServiceChain.objects.get(
                description='Create single SIP and continue processing'
            )
            result = client.execute(job.pk, chain.pk, request.user.id)

            response['message'] = 'SIP created.'
        except:
            response['error']   = True
            response['message'] = 'Error attempting to create SIP.'
    else:
        response['error']   = True
        response['message'] = 'Must be logged in.'

    return HttpResponse(
        simplejson.JSONEncoder(encoding='utf-8').encode(response),
        mimetype='application/json'
    )

def transfer_file_download(request, uuid):
    # get file basename
    try:
        file = models.File.objects.get(uuid=uuid)
    except:
        raise Http404

    file_basename = os.path.basename(file.currentlocation)

    # replace this with a helper function
    clientConfigFilePath = '/etc/archivematica/MCPServer/serverConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)

    try:
        shared_directory_path = config.get('MCPServer', 'sharedDirectory')
    except:
        shared_directory_path = ''

    transfer = models.Transfer.objects.get(uuid=file.transfer.uuid)
    path_to_transfer = transfer.currentlocation.replace('%sharedPath%', shared_directory_path)
    path_to_file = file.currentlocation.replace('%transferDirectory%', path_to_transfer)
    return send_file(request, path_to_file)
