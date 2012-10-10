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

from django.db.models import Max
from django.conf import settings as django_settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db import connection, transaction
from django.forms.models import modelformset_factory, inlineformset_factory
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson
from django.template import RequestContext
from django.utils.dateformat import format
from views_NormalizationReport import getNormalizationReportQuery
from contrib.mcp.client import MCPClient
from contrib import utils
from main import forms
from main import models
from main import filesystem
from lxml import etree
from lxml import objectify
import calendar
import cPickle
from datetime import datetime
import os
import re
import subprocess
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
from django.contrib.auth.decorators import user_passes_test
import urllib
import components.decorators as decorators

# Used for raw SQL queries to return data in dictionaries instead of lists
def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Home
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def home(request):
    return HttpResponseRedirect(reverse('main.views.transfer_grid'))

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Status
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

# TODO: hide removed elements
def status(request):
    client = MCPClient()
    xml = etree.XML(client.list())

    sip_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="SIP"]'))
    transfer_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="Transfer"]'))
    dip_count = len(xml.xpath('//choicesAvailableForUnits/choicesAvailableForUnit/unit/type[text()="DIP"]'))

    response = {'sip': sip_count, 'transfer': transfer_count, 'dip': dip_count}

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Ingest
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def ingest_grid(request):
    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    return render(request, 'main/ingest/grid.html', locals())

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
            jobs = get_jobs_by_sipuuid(item['sipuuid'])
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
                newJob['type'] = job.jobtype #map_known_values(job.jobtype)
                newJob['microservicegroup'] = job.microservicegroup
                newJob['subjobof'] = job.subjobof
                newJob['currentstep'] = job.currentstep #map_known_values(job.currentstep)
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

@decorators.load_jobs # Adds jobs, name
def ingest_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    # types = { 'ingest': 1, 'transfer': 2, 'file': 3 }
    metadata = models.DublinCore.objects.filter(metadataappliestotype__exact=1, metadataappliestoidentifier__exact=uuid)

    return render(request, 'main/ingest/metadata_list.html', locals())

def ingest_metadata_edit(request, uuid, id=None):
    if id:
        dc = models.DublinCore.objects.get(pk=id)
    else:
        # Right now we only support linking metadata to the Ingest
        try:
            dc = models.DublinCore.objects.get_sip_metadata(uuid)
            return HttpResponseRedirect(reverse('main.views.ingest_metadata_edit', args=[uuid, dc.id]))
        except ObjectDoesNotExist:
            dc = models.DublinCore(metadataappliestotype=1, metadataappliestoidentifier=uuid)

    fields = ['title', 'creator', 'subject', 'description', 'publisher',
              'contributor', 'date', 'type', 'format', 'identifier',
              'source', 'relation', 'language', 'coverage', 'rights']

    if request.method == 'POST':
        form = forms.DublinCoreMetadataForm(request.POST)
        if form.is_valid():
            for item in fields:
                setattr(dc, item, form.cleaned_data[item])
            dc.save()
            return HttpResponseRedirect(reverse('main.views.ingest_metadata_list', args=[uuid]))
    else:
        initial = {}
        for item in fields:
            initial[item] = getattr(dc, item)
        form = forms.DublinCoreMetadataForm(initial=initial)
        jobs = models.Job.objects.filter(sipuuid=uuid)
        name = utils.get_directory_name(jobs[0])

    return render(request, 'main/ingest/metadata_edit.html', locals())

def ingest_metadata_delete(request, uuid, id):
    try:
        models.DublinCore.objects.get(pk=id).delete()
        return HttpResponseRedirect(reverse('main.views.ingest_detail', args=[uuid]))
    except:
        raise Http404

def ingest_detail(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    is_waiting = jobs.filter(currentstep='Awaiting decision').count() > 0
    name = utils.get_directory_name(jobs[0])
    return render(request, 'main/ingest/detail.html', locals())

def ingest_microservices(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = utils.get_directory_name(jobs[0])
    return render(request, 'main/ingest/microservices.html', locals())

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


def ingest_normalization_report(request, uuid):
    query = getNormalizationReportQuery()
    cursor = connection.cursor()
    cursor.execute(query, ( uuid, uuid, uuid, uuid, uuid, uuid, uuid, uuid ))
    objects = dictfetchall(cursor)

    return render(request, 'main/normalization_report.html', locals())

def ingest_browse_normalization(request, jobuuid):
    jobs = models.Job.objects.filter(jobuuid=jobuuid)
    job = jobs[0]
    title = 'Review normalization'
    name = utils.get_directory_name(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/approveNormalization'

    return render(request, 'main/ingest/aip_browse.html', locals())

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
    jobs = models.Job.objects.filter(jobuuid=jobuuid)
    job = jobs[0]
    title = 'Review AIP'
    name = utils.get_directory_name(job)
    directory = '/var/archivematica/sharedDirectory/watchedDirectories/storeAIP'

    return render(request, 'main/ingest/aip_browse.html', locals())

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Transfer
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def transfer_grid(request):
    if models.SourceDirectory.objects.count() > 0:
        source_directories = models.SourceDirectory.objects.all()

    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    return render(request, 'main/transfer/grid.html', locals())

def transfer_browser(request):
    originals_directory = '/var/archivematica/sharedDirectory/transferBackups/originals'
    arrange_directory = '/var/archivematica/sharedDirectory/transferBackups/arrange'
    if not os.path.exists(originals_directory):
        os.mkdir(directory)
    if not os.path.exists(arrange_directory):
        os.mkdir(arrange_directory)
    return render(request, 'main/transfer/browser.html', locals())

def transfer_status(request, uuid=None):
    # Equivalent to: "SELECT SIPUUID, MAX(createdTime) AS latest FROM Jobs GROUP BY SIPUUID
    objects = models.Job.objects.filter(hidden=False, subjobof='', unittype__exact='unitTransfer').values('sipuuid').annotate(timestamp=Max('createdtime')).exclude(sipuuid__icontains = 'None')
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
            if models.Transfer.objects.is_hidden(item['sipuuid']):
                continue
            jobs = get_jobs_by_sipuuid(item['sipuuid'])
            item['directory'] = os.path.basename(utils.get_directory_name(jobs[0]))
            item['timestamp'] = calendar.timegm(item['timestamp'].timetuple())
            item['uuid'] = item['sipuuid']
            item['id'] = item['sipuuid']
            del item['sipuuid']
            item['jobs'] = []
            for job in jobs:
                newJob = {}
                item['jobs'].append(newJob)
                newJob['uuid'] = job.jobuuid
                newJob['type'] = job.jobtype #map_known_values(job.jobtype)
                newJob['microservicegroup'] = job.microservicegroup
                newJob['subjobof'] = job.subjobof
                newJob['currentstep'] = job.currentstep #map_known_values(job.currentstep)
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

def transfer_detail(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = utils.get_directory_name(jobs[0])
    is_waiting = jobs.filter(currentstep='Awaiting decision').count() > 0
    return render(request, 'main/transfer/detail.html', locals())

def transfer_microservices(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = utils.get_directory_name(jobs[0])
    return render(request, 'main/transfer/microservices.html', locals())

def transfer_delete(request, uuid):
    try:
        transfer = models.Transfer.objects.get(uuid__exact=uuid)
        transfer.hidden = True
        transfer.save()
        response = simplejson.JSONEncoder().encode({'removed': True})
        return HttpResponse(response, mimetype='application/json')
    except:
        raise Http404

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Access
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def access_list(request):
    access = models.Access.objects.all()
    return render(request, 'main/access.html', locals())

def access_delete(request, id):
    access = get_object_or_404(models.Access, pk=id)
    access.delete()
    return HttpResponseRedirect(reverse('main.views.access_list'))

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def administration(request):
    return HttpResponseRedirect(reverse('main.views.administration_dip'))

def administration_search(request):
    message = request.GET.get('message', '')
    aip_files_indexed = archival_storage_indexed_count('aips')
    return render(request, 'main/administration/search.html', locals())

def administration_search_flush_aips_context(request):
    prompt = 'Flush AIP search index?'
    cancel_url = reverse("main.views.administration_search")
    return RequestContext(request, {'action': 'Flush', 'prompt': prompt, 'cancel_url': cancel_url})

@decorators.confirm_required('simple_confirm.html', administration_search_flush_aips_context)
@user_passes_test(lambda u: u.is_superuser, login_url='/forbidden/')
def administration_search_flush_aips(request):
    conn = pyes.ES('127.0.0.1:9200')
    index = 'aips'

    try:
        conn.delete_index(index)
        message = 'AIP search index flushed.'
        try:
            conn.create_index(index)
        except pyes.exceptions.IndexAlreadyExistsException:
            message = 'Error recreating AIP search index.'

    except:
        message = 'Error flushing AIP search index.'
        pass

    params = urllib.urlencode({'message': message})
    return HttpResponseRedirect(reverse("main.views.administration_search") + "?%s" % params)

def administration_dip(request):
    upload_setting = models.StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    return render(request, 'main/administration/dip.html', locals())

def administration_dip_edit(request, id):
    if request.method == 'POST':
        upload_setting = models.StandardTaskConfig.objects.get(pk=id)
        form = forms.AdministrationForm(request.POST)
        if form.is_valid():
            upload_setting.arguments = form.cleaned_data['arguments']
            upload_setting.save()

    return HttpResponseRedirect(reverse("main.views.administration_dip"))

def administration_atom_dips(request):
    link_id = administration_atom_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'main/administration/dips_edit.html', locals())

def administration_contentdm_dips(request):
    link_id = administration_contentdm_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'main/administration/dips_contentdm_edit.html', locals())

def administration_atom_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select DIP upload destination')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_contentdm_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select target CONTENTdm server')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_dips_formset():
    return modelformset_factory(
        models.MicroServiceChoiceReplacementDic,
        form=forms.MicroServiceChoiceReplacementDicForm,
        extra=1,
        can_delete=True
    )

def administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet):
    valid_submission = True
    formset = None

    if request.method == 'POST':
        formset = ReplaceDirChoiceFormSet(request.POST)

        # take note of formset validity because if submission was successful
        # we reload it to reflect
        # deletions, etc.
        valid_submission = formset.is_valid()

        if valid_submission:
            # save/delete partial data (without association with specific link)
            instances = formset.save()

            # restore link association
            for instance in instances:
                instance.choiceavailableatlink = link_id
                instance.save()
    return valid_submission, formset

def administration_sources(request):
    return render(request, 'main/administration/sources.html', locals())

def administration_sources_json(request):
    message = ''
    if request.method == 'POST':
         path = request.POST.get('path', '')
         if path != '':
              try:
                  models.SourceDirectory.objects.get(path=path)
              except models.SourceDirectory.DoesNotExist:
                  # save dir
                  source_dir = models.SourceDirectory()
                  source_dir.path = path
                  source_dir.save()
                  message = 'Directory added.'
              else:
                  message = 'Directory already added.'
         else:
              message = 'Path is empty.'

    response = {}
    response['message'] = message
    response['directories'] = []

    for directory in models.SourceDirectory.objects.all():
      response['directories'].append({
        'id':   directory.id,
        'path': directory.path
      })
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def administration_sources_delete_json(request, id):
    models.SourceDirectory.objects.get(pk=id).delete()
    response = {}
    response['message'] = 'Deleted.'
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')
    #return HttpResponseRedirect(reverse('main.views.administration_sources'))

def administration_processing(request):
    file_path = '/var/archivematica/sharedDirectory/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml'

    if request.method == 'POST':
        xml = request.POST.get('xml', '')
        file = open(file_path, 'w')
        file.write(xml)
    else:
        file = open(file_path, 'r')
        xml = file.read()

    return render(request, 'main/administration/processing.html', locals())

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Misc
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def forbidden(request):
    return render(request, 'forbidden.html')

def task_duration_in_seconds(task):
    duration = int(format(task.endtime, 'U')) - int(format(task.starttime, 'U'))
    if duration == 0:
        duration = '< 1'
    return duration

def task(request, uuid):
    task = models.Task.objects.get(taskuuid=uuid)
    task.duration = task_duration_in_seconds(task)
    objects = [task]
    return render(request, 'main/tasks.html', locals())

def tasks(request, uuid):
    job = models.Job.objects.get(jobuuid=uuid)
    objects = job.task_set.all().order_by('-exitcode', '-endtime', '-starttime', '-createdtime')

    # figure out duration in seconds
    for object in objects:
         object.duration = task_duration_in_seconds(object)

    return render(request, 'main/tasks.html', locals())

def map_known_values(value):
    #changes should be made in the database, not this map
    map = {
      # currentStep
      'completedSuccessfully': 'Completed successfully',
      'completedUnsuccessfully': 'Failed',
      'exeCommand': 'Executing command(s)',
      'verificationCommand': 'Executing command(s)',
      'requiresAprroval': 'Requires approval',
      'requiresApproval': 'Requires approval',
      # jobType
      'acquireSIP': 'Acquire SIP',
      'addDCToMETS': 'Add DC to METS',
      'appraiseSIP': 'Appraise SIP',
      'assignSIPUUID': 'Asign SIP UUID',
      'assignUUID': 'Assign file UUIDs and checksums',
      'bagit': 'Bagit',
      'cleanupAIPPostBagit': 'Cleanup AIP post bagit',
      'compileMETS': 'Compile METS',
      'copyMETSToDIP': 'Copy METS to DIP',
      'createAIPChecksum': 'Create AIP checksum',
      'createDIPDirectory': 'Create DIP directory',
      'createOrMoveDC': 'Create or move DC',
      'createSIPBackup': 'Create SIP backup',
      'detoxFileNames': 'Detox filenames',
      'extractPackage': 'Extract package',
      'FITS': 'FITS',
      'normalize': 'Normalize',
      'Normalization Failed': 'Normalization failed',
      'quarantine': 'Place in quarantine',
      'reviewSIP': 'Review SIP',
      'scanForRemovedFilesPostAppraiseSIPForPreservation': 'Scan for removed files post appraise SIP for preservation',
      'scanForRemovedFilesPostAppraiseSIPForSubmission': 'Scan for removed files post appraise SIP for submission',
      'scanWithClamAV': 'Scan with ClamAV',
      'seperateDIP': 'Seperate DIP',
      'storeAIP': 'Store AIP',
      'unquarantine': 'Remove from Quarantine',
      'Upload DIP': 'Upload DIP',
      'verifyChecksum': 'Verify checksum',
      'verifyMetadataDirectoryChecksums': 'Verify metadata directory checksums',
      'verifySIPCompliance': 'Verify SIP compliance',
    }
    if value in map:
        return map[value]
    else:
        return value

def get_jobs_by_sipuuid(uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid).order_by('-createdtime')
    priorities = {
        'completedUnsuccessfully': 0,
        'requiresAprroval': 1,
        'requiresApproval': 1,
        'exeCommand': 2,
        'verificationCommand': 3,
        'completedSuccessfully': 4,
        'cleanupSuccessfulCommand': 5,
    }
    def get_priority(job):
        try: return priorities[job.currentstep]
        except Exception: return 0
    return sorted(jobs, key = get_priority) # key = lambda job: priorities[job.currentstep]

def jobs_list_objects(request, uuid):
    response = []
    job = models.Job.objects.get(jobuuid=uuid)

    for root, dirs, files in os.walk(job.directory + '/objects', False):
        for name in files:
            directory = root.replace(job.directory + '/objects', '')
            response.append(os.path.join(directory, name))

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def jobs_explore(request, uuid):
    # Database query
    job = models.Job.objects.get(jobuuid=uuid)
    # Prepare response object
    contents = []
    response = {}
    response['contents'] = contents
    # Parse request
    if 'path' in request.REQUEST and len(request.REQUEST['path']) > 0:
        directory = os.path.join(job.directory, request.REQUEST['path'])
        response['base'] = request.REQUEST['path'].replace('.', '')
    else:
        directory = job.directory
        response['base'] = ''
    # Build directory
    directory = os.path.abspath(directory)
    # Security check
    tmpDirectory = os.path.realpath(directory)
    while True:
        if tmpDirectory == os.path.realpath(job.directory):
            break
        elif tmpDirectory == '/':
            raise Http404
        else:
            tmpDirectory = os.path.dirname(tmpDirectory)
    # If it is a file, return the contents
    if os.path.isfile(directory):
        mime = subprocess.Popen('/usr/bin/file --mime-type ' + directory, shell=True, stdout=subprocess.PIPE).communicate()[0].split(' ')[-1].strip()
        response = HttpResponse(mimetype=mime)
        response['Content-Disposition'] = 'attachment; filename=%s' %  os.path.basename(directory)
        with open(directory) as resource:
            response.write(resource.read())
        return response
    # Cleaning path
    parentDir = os.path.dirname(directory)
    parentDir = parentDir.replace('%s/' % job.directory, '')
    parentDir = parentDir.replace('%s' % job.directory, '')
    response['parent'] = parentDir
    # Check if it is or not the root dir to add the "Go parent" link
    if os.path.realpath(directory) != os.path.realpath(job.directory):
        parent = {}
        parent['name'] = 'Go to parent directory...'
        parent['type'] = 'parent'
        contents.append(parent)
    # Add contents of the directory
    for item in os.listdir(directory):
        newItem = {}
        newItem['name'] = item
        if os.path.isdir(os.path.join(directory, item)):
            newItem['type'] = 'dir'
        else:
            newItem['type'] = 'file'
            newItem['size'] = os.path.getsize(os.path.join(directory, item))
        contents.append(newItem)
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def formdata_delete(request, type, parent_id, delete_id):
  return formdata(request, type, parent_id, delete_id)

def formdata(request, type, parent_id, delete_id = None):
    model    = None
    results  = None
    response = {}

    # define types handled
    if (type == 'rightsnote'):
        model = models.RightsStatementRightsGrantedNote
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = 'rightsgranted'
        model_value_fields = ['rightsgrantednote']

        results = model.objects.filter(rightsgranted=parent_id)

    if (type == 'rightsrestriction'):
        model = models.RightsStatementRightsGrantedRestriction
        parent_model = models.RightsStatementRightsGranted
        model_parent_field = 'rightsgranted'
        model_value_fields = ['restriction']

        results = model.objects.filter(rightsgranted=parent_id)

    if (type == 'licensenote'):
        model = models.RightsStatementLicenseNote
        parent_model = models.RightsStatementLicense
        model_parent_field = 'rightsstatementlicense'
        model_value_fields = ['licensenote']

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if (type == 'statutenote'):
        model = models.RightsStatementStatuteInformationNote
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = 'rightsstatementstatute'
        model_value_fields = ['statutenote']

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if (type == 'copyrightnote'):
        model = models.RightsStatementCopyrightNote
        parent_model = models.RightsStatementCopyright
        model_parent_field = 'rightscopyright'
        model_value_fields = ['copyrightnote']

        results = model.objects.filter(rightscopyright=parent_id)

    if (type == 'copyrightdocumentationidentifier'):
        model = models.RightsStatementCopyrightDocumentationIdentifier
        parent_model = models.RightsStatementCopyright
        model_parent_field = 'rightscopyright'
        model_value_fields = [
          'copyrightdocumentationidentifiertype',
          'copyrightdocumentationidentifiervalue',
          'copyrightdocumentationidentifierrole'
        ]

        results = model.objects.filter(rightscopyright=parent_id)

    if (type == 'statutedocumentationidentifier'):
        model = models.RightsStatementStatuteDocumentationIdentifier
        parent_model = models.RightsStatementStatuteInformation
        model_parent_field = 'rightsstatementstatute'
        model_value_fields = [
          'statutedocumentationidentifiertype',
          'statutedocumentationidentifiervalue',
          'statutedocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementstatute=parent_id)

    if (type == 'licensedocumentationidentifier'):
        model = models.RightsStatementLicenseDocumentationIdentifier
        parent_model = models.RightsStatementLicense
        model_parent_field = 'rightsstatementlicense'
        model_value_fields = [
          'licensedocumentationidentifiertype',
          'licensedocumentationidentifiervalue',
          'licensedocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementlicense=parent_id)

    if (type == 'otherrightsdocumentationidentifier'):
        model = models.RightsStatementOtherRightsDocumentationIdentifier
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = 'rightsstatementotherrights'
        model_value_fields = [
          'otherrightsdocumentationidentifiertype',
          'otherrightsdocumentationidentifiervalue',
          'otherrightsdocumentationidentifierrole'
        ]

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    if (type == 'otherrightsnote'):
        model = models.RightsStatementOtherRightsInformationNote
        parent_model = models.RightsStatementOtherRightsInformation
        model_parent_field = 'rightsstatementotherrights'
        model_value_fields = ['otherrightsnote']

        results = model.objects.filter(rightsstatementotherrights=parent_id)

    # handle creation
    if (request.method == 'POST'):
        # load or initiate model instance
        id = request.POST.get('id', 0)
        if id > 0:
            instance = model.objects.get(pk=id)
        else:
            instance = model()

        # set instance parent
        parent = parent_model.objects.filter(pk=parent_id)
        setattr(instance, model_parent_field, parent[0])

        # set instance field values using request data
        for field in model_value_fields:
            value = request.POST.get(field, '')
            setattr(instance, field, value)
        instance.save()

        if id == 0:
          response['new_id']  = instance.pk

        response['message'] = 'Added.'

    # handle deletion
    if (request.method == 'DELETE'):
        if (delete_id == None):
            response['message'] = 'Error: no delete ID supplied.'
        else:
            model.objects.filter(pk=delete_id).delete()
            response['message'] = 'Deleted.'

    # send back revised data
    if (results != None):
        response['results'] = []
        for result in results:
            values = {}
            for field in model_value_fields:
                values[field] = result.__dict__[field]
            response['results'].append({
              'id': result.pk,
              'values': values
            });

    if (model == None):
        response['message'] = 'Incorrect type.'

    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def chain_insert():
    # first choice
    standardTaskConfig = models.StandardTaskConfig()
    standardTaskConfig.save()

    taskConfig = models.TaskConfig()
    taskConfig.tasktype = 5
    taskConfig.tasktypepkreference = standardTaskConfig.id
    taskConfig.description = 'Select DIP upload destination'
    taskConfig.save()

    link = models.MicroServiceChainLink()
    link.microservicegroup = 'Upload DIP'
    link.currenttask = taskConfig.id
    link.save()
    choice_link_id = link.id

    choice = models.MicroServiceChoiceReplacementDic()
    choice.choiceavailableatlink = link.id
    choice.description = 'Test dict 1'
    choice.replacementdic = '{}'
    choice.save()

    choice = models.MicroServiceChoiceReplacementDic()
    choice.choiceavailableatlink = link.id
    choice.description = 'Test dict 2'
    choice.replacementdic = '{}'
    choice.save()

    # take note of ID of existing chain to points to ICA AtoM DIP upload links
    #chains = models.MicroServiceChain.objects.filter(description='Upload DIP to ICA-ATOM')
    #chain = chains[0]
    #upload_start_link_id = chain.startinglink
    #chain.startinglink = choice_link_id
    #chain.description = 'Select Upload Destination'
    #chain.save()


    # make new chain to point to ICA AtoM DIP upload links
    chain = models.MicroServiceChain()
    chain.startinglink = choice_link_id
    chain.description = 'Select DIP destination'
    chain.save()

    # rewire old choice to point to new chain
    choices = models.MicroServiceChainChoice.objects.filter(chainavailable=23)
    choice = choices[0]
    choice.chainavailable = chain.id
    choice.save()

    # add exit code to the choice link that points to the Qubit upload link
    code = models.MicroServiceChainLinkExitCode()
    code.exitcode = 0
    code.microservicechainlink = choice_link_id
    code.nextmicroservicechainlink = 4
    code.exitmessage = 'Completed successfully'
    code.save()
    

