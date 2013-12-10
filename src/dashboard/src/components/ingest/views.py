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
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.contrib import messages
import json
from contrib.mcp.client import MCPClient
from contrib import utils
from main import forms
from main import models
from lxml import etree
from components.ingest.forms import DublinCoreMetadataForm
from components.ingest.views_NormalizationReport import getNormalizationReportQuery
from components import helpers
import calendar, ConfigParser, socket, uuid
import cPickle
import components.decorators as decorators
from django.template import RequestContext
from components import helpers
from components import advanced_search
import os, sys, MySQLdb, shutil
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions, databaseInterface, databaseFunctions
from archivematicaCreateStructuredDirectory import createStructuredDirectory
from archivematicaCreateStructuredDirectory import createManualNormalizedDirectoriesList
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes, requests
from components.archival_storage.forms import StorageSearchForm
import time

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

@decorators.elasticsearch_required()
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
        metadataappliestotype__exact=ingest_sip_metadata_type_id(),
        metadataappliestoidentifier__exact=uuid
    )

    return render(request, 'ingest/metadata_list.html', locals())

def ingest_metadata_edit(request, uuid, id=None):
    if id:
        dc = models.DublinCore.objects.get(pk=id)
    else:
        # Right now we only support linking metadata to the Ingest
        try:
            dc = models.DublinCore.objects.get_sip_metadata(uuid)
            return redirect('components.ingest.views.ingest_metadata_edit', uuid, dc.id)
        except ObjectDoesNotExist:
            dc = models.DublinCore(
                metadataappliestotype=ingest_sip_metadata_type_id(),
                metadataappliestoidentifier=uuid
            )

    fields = ['title', 'creator', 'subject', 'description', 'publisher',
              'contributor', 'date', 'type', 'format', 'identifier',
              'source', 'relation', 'language', 'coverage', 'rights']

    if request.method == 'POST':
        form = DublinCoreMetadataForm(request.POST)
        if form.is_valid():
            for item in fields:
                setattr(dc, item, form.cleaned_data[item])
            dc.save()
            return redirect('components.ingest.views.ingest_metadata_list', uuid)
    else:
        initial = {}
        for item in fields:
            initial[item] = getattr(dc, item)
        form = DublinCoreMetadataForm(initial=initial)
        jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
        name = utils.get_directory_name_from_job(jobs[0])

    return render(request, 'ingest/metadata_edit.html', locals())

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

@decorators.elasticsearch_required()
def transfer_backlog(request):
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
            'components.ingest.views.transfer_backlog',
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
    conn = elasticSearchFunctions.connect_and_create_index('transfers')

    try:
        query = advanced_search.assemble_query(
            queries,
            ops,
            fields,
            types,
            must_haves=[pyes.TermQuery('status', 'backlog')]
        )

        # use all results to pull transfer facets if not in file mode
        if not file_mode:
            results = conn.search_raw(
                query,
                indices='transfers',
                type='transferfile',
            )
        else:
        # otherwise use pages results
            results = conn.search_raw(
                query,
                indices='transfers',
                type='transferfile',
                start=start - 1,
                size=items_per_page
            )
    except:
        return HttpResponse('Error accessing index.')

    # take note of facet data
    file_extension_usage = results['facets']['fileExtension']['terms']
    transfer_uuids       = results['facets']['sipuuid']['terms']

    if not file_mode:
        # run through transfers to see if they've been created yet
        awaiting_creation = {}
        for transfer_instance in transfer_uuids:
            try:
                awaiting_creation[transfer_instance.term] = transfer_awaiting_sip_creation_v2(transfer_instance.term)
                transfer = models.Transfer.objects.get(uuid=transfer_instance.term)
                transfer_basename = os.path.basename(transfer.currentlocation[:-1])
                transfer_instance.name = transfer_basename[:-37]
                if transfer.accessionid != None:
                    transfer_instance.accession = transfer.accessionid
                else:
                    transfer_instance.accession = ''
            except:
                awaiting_creation[transfer_instance.term] = False

        # page data
        number_of_results = len(transfer_uuids)
        page_data = helpers.pager(transfer_uuids, items_per_page, page + 1)
        transfer_uuids = page_data['objects']
    else:
        # page data
        number_of_results = results.hits.total
        results = transfer_backlog_augment_search_results(results)

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

def transfer_awaiting_sip_creation_v2(uuid):
    transfer = models.Transfer.objects.get(uuid=uuid)
    return transfer.currentlocation.find('%sharedPath%www/AIPsStore/transferBacklog/originals/') == 0

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

def process_transfer(request, transfer_uuid):
    response = {}

    if request.user.id:
        # get transfer info
        transfer = models.Transfer.objects.get(uuid=transfer_uuid)
        transfer_path = transfer.currentlocation.replace(
            '%sharedPath%',
            helpers.get_server_config_value('sharedDirectory')
        )

        createStructuredDirectory(transfer_path, createManualNormalizedDirectories=False)

        processingDirectory = helpers.get_server_config_value('processingDirectory')
        transfer_directory_name = os.path.basename(transfer_path[:-1])
        transfer_name = transfer_directory_name[:-37]
        sharedPath = helpers.get_server_config_value('sharedDirectory')

        tmpSIPDir = os.path.join(processingDirectory, transfer_name) + "/"
        processSIPDirectory = os.path.join(sharedPath, 'watchedDirectories/SIPCreation/SIPsUnderConstruction') + '/'

        createStructuredDirectory(tmpSIPDir, createManualNormalizedDirectories=False)
        objectsDirectory = os.path.join(transfer_path, 'objects') + '/'

        sipUUID = uuid.uuid4().__str__()
        destSIPDir = os.path.join(processSIPDirectory, transfer_name) + "/"
        lookup_path = destSIPDir.replace(sharedPath, '%sharedPath%')
        databaseFunctions.createSIP(lookup_path, sipUUID)

        #move the objects to the SIPDir
        for item in os.listdir(objectsDirectory):
            shutil.move(os.path.join(objectsDirectory, item), os.path.join(tmpSIPDir, "objects", item))

        #get the database list of files in the objects directory
        #for each file, confirm it's in the SIP objects directory, and update the current location/ owning SIP'
        sql = """SELECT  fileUUID, currentLocation FROM Files WHERE removedTime = 0 AND currentLocation LIKE '\%transferDirectory\%objects%' AND transferUUID =  '""" + transfer_uuid + "'"
        for row in databaseInterface.queryAllSQL(sql):
            fileUUID = row[0]
            currentPath = databaseFunctions.deUnicode(row[1])
            currentSIPFilePath = currentPath.replace("%transferDirectory%", tmpSIPDir)
            if os.path.isfile(currentSIPFilePath):
                sql = """UPDATE Files SET currentLocation='%s', sipUUID='%s' WHERE fileUUID='%s'""" % (MySQLdb.escape_string(currentPath.replace("%transferDirectory%", "%SIPDirectory%")), sipUUID, fileUUID)
                databaseInterface.runSQL(sql)
            else:
                print >>sys.stderr, "file not found: ", currentSIPFilePath

        #copy processingMCP.xml file
        src = os.path.join(os.path.dirname(objectsDirectory[:-1]), "processingMCP.xml")
        dst = os.path.join(tmpSIPDir, "processingMCP.xml")
        shutil.copy(src, dst)

        #moveSIPTo processSIPDirectory
        shutil.move(tmpSIPDir, destSIPDir)

        elasticSearchFunctions.connect_and_change_transfer_file_status(transfer_uuid, '')

        # move original files to completed transfers
        completed_directory = os.path.join(sharedPath, 'watchedDirectories/SIPCreation/completedTransfers')
        shutil.move(transfer_path, completed_directory)

        # update DB
        transfer.currentlocation = '%sharedPath%/watchedDirectories/SIPCreation/completedTransfers/' + transfer_name + '-' + transfer_uuid + '/'
        transfer.save()

        response['message'] = 'SIP ' + sipUUID + ' created.'
    else:
        response['error']   = True
        response['message'] = 'Must be logged in.'

    return helpers.json_response(response)

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
