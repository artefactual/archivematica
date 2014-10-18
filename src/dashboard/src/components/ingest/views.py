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

# Standard library, alphabetical by import source
import base64
import calendar
import cPickle
import json
import logging
from lxml import etree
import os
import shutil
import socket
import sys

# Django Core, alphabetical by import source
from django.conf import settings as django_settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils.text import slugify

# External dependencies, alphabetical

# This project, alphabetical by import source
from contrib import utils
from contrib.mcp.client import MCPClient
from components import advanced_search
from components import helpers
from components import decorators
from components.ingest import forms as ingest_forms
from components.ingest.views_NormalizationReport import getNormalizationReportQuery
from main import forms
from main import models

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import elasticSearchFunctions
import storageService as storage_service


sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

@decorators.elasticsearch_required()
def ingest_grid(request):
    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    uid = request.user.id

    try:
        storage_service.get_location(purpose="BL")
    except:
        messages.warning(request, 'Error retrieving originals/arrange directory locations: is the storage server running? Please contact an administrator.')

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
            item['directory'] = utils.get_directory_name_from_job(jobs[0])
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

    return HttpResponse(
        json.JSONEncoder(default=encoder).encode(response),
        mimetype='application/json'
    )

def ingest_sip_metadata_type_id():
    return helpers.get_metadata_type_id_by_description('SIP')

@decorators.load_jobs # Adds jobs, name
def ingest_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    metadata = models.DublinCore.objects.filter(
        metadataappliestotype=ingest_sip_metadata_type_id(),
        metadataappliestoidentifier__exact=uuid
    )

    return render(request, 'ingest/metadata_list.html', locals())

def ingest_metadata_edit(request, uuid, id=None):
    if id:
        # If we have the ID of the DC object, use that - Edit
        dc = models.DublinCore.objects.get(pk=id)
    else:
        # Otherwise look for a SIP with the provided UUID, creating a new one
        # if needed.  Not using get_or_create because that save the empty
        # object, even if the form is not submitted.
        sip_type_id = ingest_sip_metadata_type_id()
        try:
            dc = models.DublinCore.objects.get(
                metadataappliestotype=sip_type_id,
                metadataappliestoidentifier=uuid)
            id = dc.id
        except models.DublinCore.DoesNotExist:
            dc = models.DublinCore(
                metadataappliestotype=sip_type_id,
                metadataappliestoidentifier=uuid)

    # If the SIP is an AIC, use the AIC metadata form
    if models.SIP.objects.get(uuid=uuid).sip_type == 'AIC':
        form = ingest_forms.AICDublinCoreMetadataForm(request.POST or None,
            instance=dc)
        dc_type = "Archival Information Collection"
    else:
        form = ingest_forms.DublinCoreMetadataForm(request.POST or None,
            instance=dc)
        dc_type = "Archival Information Package"

    if form.is_valid():
        dc = form.save()
        dc.type = dc_type
        dc.save()
        return redirect('components.ingest.views.ingest_metadata_list', uuid)
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs[0])

    return render(request, 'ingest/metadata_edit.html', locals())


def ingest_metadata_add_files(request, sip_uuid):
    try:
        source_directories = storage_service.get_location(purpose="TS")
    except:
        messages.warning(request, 'Error retrieving source directories: is the storage server running? Please contact an administrator.')
    else:
        logging.debug("Source directories found: {}".format(source_directories))
        if not source_directories:
            msg = "No transfer source locations are available. Please contact an administrator."
            messages.warning(request, msg)
    # Get name of SIP from directory name of most recent job
    # Making list and slicing for speed: http://stackoverflow.com/questions/5123839/fastest-way-to-get-the-first-object-from-a-queryset-in-django
    jobs = list(models.Job.objects.filter(sipuuid=sip_uuid, subjobof='')[:1])
    name = utils.get_directory_name_from_job(jobs[0])

    return render(request, 'ingest/metadata_add_files.html', locals())


def aic_metadata_add(request, uuid):
    sip_type_id = ingest_sip_metadata_type_id()
    try:
        dc = models.DublinCore.objects.get(
            metadataappliestotype=sip_type_id,
            metadataappliestoidentifier=uuid)
        id = dc.id
    except models.DublinCore.DoesNotExist:
        dc = models.DublinCore(
            metadataappliestotype=sip_type_id,
            metadataappliestoidentifier=uuid)

    form = ingest_forms.AICDublinCoreMetadataForm(request.POST or None, instance=dc)
    if form.is_valid():
        # Save the metadata
        dc = form.save()
        dc.type = "Archival Information Collection"
        dc.save()

        # Start the MicroServiceChainLink for the AIC
        shared_dir = helpers.get_server_config_value('sharedDirectory')
        source = os.path.join(shared_dir, 'tmp', uuid)

        watched_dir = helpers.get_server_config_value('watchDirectoryPath')
        name = dc.title if dc.title else dc.identifier
        name = slugify(name).replace('-', '_')
        dir_name = '{name}-{uuid}'.format(name=name, uuid=uuid)
        destination = os.path.join(watched_dir, 'system', 'createAIC', dir_name)

        destination_db = destination.replace(shared_dir, '%sharedPath%')+'/'
        models.SIP.objects.filter(uuid=uuid).update(currentpath=destination_db)
        shutil.move(source, destination)
        return redirect('ingest_index')

    name = dc.title or "New AIC"
    aic = True
    return render(request, 'ingest/metadata_edit.html', locals())

def ingest_metadata_event_detail(request, uuid):
    EventDetailFormset = modelformset_factory(models.Event, form=forms.EventDetailForm, extra=0)
    manual_norm_files = models.File.objects.filter(sip=uuid).filter(originallocation__icontains='manualNormalization/preservation')
    events = models.Event.objects.filter(derivation__derived_file__in=manual_norm_files).order_by('file_uuid__currentlocation')
    formset = EventDetailFormset(request.POST or None, queryset=events)

    if formset.is_valid():
        formset.save()
        return redirect('components.ingest.views.ingest_detail', uuid)

    # Add path for original and derived files to each form
    for form in formset:
        form.original_file = form.instance.file_uuid.originallocation.replace("%transferDirectory%objects/", "", 1)
        form.derived_file = form.instance.file_uuid.derived_file_set.get().derived_file.originallocation.replace("%transferDirectory%objects/", "", 1)

    # Get name of SIP from directory name of most recent job
    # Making list and slicing for speed: http://stackoverflow.com/questions/5123839/fastest-way-to-get-the-first-object-from-a-queryset-in-django
    jobs = list(models.Job.objects.filter(sipuuid=uuid, subjobof='')[:1])
    name = utils.get_directory_name_from_job(jobs[0])
    return render(request, 'ingest/metadata_event_detail.html', locals())

def delete_context(request, uuid, id):
    prompt = 'Are you sure you want to delete this metadata?'
    cancel_url = reverse("components.ingest.views.ingest_metadata_list", args=[uuid])
    return RequestContext(request, {'action': 'Delete', 'prompt': prompt, 'cancel_url': cancel_url})

@decorators.confirm_required('simple_confirm.html', delete_context)
def ingest_metadata_delete(request, uuid, id):
    try:
        models.DublinCore.objects.get(pk=id).delete()
        messages.info(request, 'Deleted.')
        return redirect('components.ingest.views.ingest_metadata_list', uuid)
    except:
        raise Http404

def ingest_detail(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    is_waiting = jobs.filter(currentstep='Awaiting decision').count() > 0
    name = utils.get_directory_name_from_job(jobs[0])
    return render(request, 'ingest/detail.html', locals())

def ingest_microservices(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs[0])
    return render(request, 'ingest/microservices.html', locals())

def ingest_delete(request, uuid):
    try:
        sip = models.SIP.objects.get(uuid__exact=uuid)
        sip.hidden = True
        sip.save()

        response = { 'removed': True }
        return helpers.json_response(response)

    except:
        raise Http404

def ingest_upload_destination_url_check(request):
    url = ''
    server_ip = socket.gethostbyname(request.META['SERVER_NAME'])

    upload_setting = models.StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    upload_arguments = upload_setting.arguments

    # this can probably be done more elegantly with a regex
    url_start = upload_arguments.find('--url')

    if url_start == -1:
        url_start = upload_arguments.find('--URL')

    if url_start != -1:
        chunk = upload_arguments[url_start:]
        value_start = chunk.find('"')
        next_chunk = chunk[value_start + 1:]
        value_end = next_chunk.find('"')
        url = next_chunk[:value_end]

    # add target to URL
    url = url + '/' + request.GET.get('target', '')

    # make request for URL
    response = requests.request('GET', url)

    # return resulting status code from request
    return HttpResponse(response.status_code)

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
              "target": request.POST['target'] })
            access.save()
            response = { 'ready': True }
            return helpers.json_response(response)
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
        return helpers.json_response(data)

    return HttpResponseBadRequest()

def ingest_normalization_report(request, uuid, current_page=None):
    jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
    job = jobs[0]
    sipname = utils.get_directory_name_from_job(job)

    objects = getNormalizationReportQuery(sipUUID=uuid)
    for o in objects:
        o['location'] = archivematicaFunctions.escape(o['location'])

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
    name = utils.get_directory_name_from_job(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/approveNormalization'

    return render(request, 'ingest/aip_browse.html', locals())

def ingest_browse_aip(request, jobuuid):
    jobs = models.Job.objects.filter(jobuuid=jobuuid, subjobof='')
    job = jobs[0]
    title = 'Review AIP'
    name = utils.get_directory_name_from_job(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/storeAIP'

    return render(request, 'ingest/aip_browse.html', locals())


def _es_results_to_directory_tree(path, return_list, not_draggable=False):
    # Helper function for transfer_backlog
    # Paths MUST be input in sorted order
    # Otherwise the same directory might end up with multiple entries
    parts = path.split('/', 1)
    if parts[0] in ('logs', 'metadata'):
        not_draggable = True
    if len(parts) == 1:  # path is a file
        return_list.append({
            'name': base64.b64encode(parts[0]),
            'not_draggable': not_draggable})
    else:
        node, others = parts
        node = base64.b64encode(node)
        if not return_list or return_list[-1]['name'] != node:
            return_list.append({
                'name': node,
                'not_draggable': not_draggable,
                'children': []})
        _es_results_to_directory_tree(others, return_list[-1]['children'],
            not_draggable=not_draggable)
        # If any children of a dir are draggable, the whole dir should be
        # Otherwise, directories have the draggability of their first child
        return_list[-1]['not_draggable'] = return_list[-1]['not_draggable'] and not_draggable


@decorators.elasticsearch_required()
def transfer_backlog(request):
    """
    AJAX endpoint to query for and return transfer backlog items.
    """
    # Get search parameters from request
    results = None
    queries, ops, fields, types = advanced_search.search_parameter_prep(request)

    # redirect if no search params have been set
    # TODO fix what to do if no request - return nothing?  All?
    if not 'query' in request.GET:
        return redirect(reverse('components.ingest.views.transfer_backlog'))

    # perform search
    conn = elasticSearchFunctions.connect_and_create_index('transfers')
    try:
        query = advanced_search.assemble_query(
            queries,
            ops,
            fields,
            types,
            must_haves={'term': {'status': 'backlog'}}
        )

        results = elasticSearchFunctions.search_raw_wrapper(
            conn,
            query=query,
            indices='transfers',
            doc_types='transferfile',
        )
    except:
        logger.exception('Error accessing index.')
        return HttpResponse('Error accessing index.')


    # Convert results into a more workable form
    results = _transfer_backlog_augment_search_results(results)

    # Convert to a form JS can use:
    # [{'name': <filename>,
    #   'not_draggable': False},
    #  {'name': <directory name>,
    #   'not_draggable': True,
    #   'children': [
    #    {'name': <filename>,
    #     'not_draggable': True},
    #    {'name': <directory name>,
    #     'children': [...]
    #    }
    #   ]
    #  },
    # ]
    return_list = []
    # _es_results_to_directory_tree requires that paths MUST be sorted
    results.sort(key=lambda x: x['relative_path'])
    for path in results:
        # If a path is in SIPArrange.original_path, then it shouldn't be draggable
        not_draggable = False
        if models.SIPArrange.objects.filter(
            original_path__endswith=path['relative_path']).exists():
            not_draggable = True
        _es_results_to_directory_tree(path['relative_path'], return_list, not_draggable=not_draggable)

    # retun JSON response
    return helpers.json_response(return_list)


def _transfer_backlog_augment_search_results(raw_results):
    modifiedResults = []

    for item in raw_results['hits']['hits']:
        clone = item['_source'].copy()
        clone['document_id'] = item[u'_id']
        modifiedResults.append(clone)

    return modifiedResults


def transfer_file_download(request, uuid):
    # get file basename
    try:
        file = models.File.objects.get(uuid=uuid)
    except:
        raise Http404

    file_basename = os.path.basename(file.currentlocation)
    shared_directory_path = helpers.get_server_config_value('sharedDirectory')
    transfer = models.Transfer.objects.get(uuid=file.transfer.uuid)
    path_to_transfer = transfer.currentlocation.replace('%sharedPath%', shared_directory_path)
    path_to_file = file.currentlocation.replace('%transferDirectory%', path_to_transfer)
    return helpers.send_file(request, path_to_file)
