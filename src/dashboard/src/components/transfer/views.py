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

import calendar
import json
import logging
from lxml import etree
import os

from django.db.models import Max
from django.conf import settings as django_settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist 
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from django.utils.safestring import mark_safe

from contrib.mcp.client import MCPClient
from contrib import utils

from main import models
from components import helpers
from components.ingest.forms import DublinCoreMetadataForm
import components.decorators as decorators
import storageService as storage_service

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log", 
    level=logging.DEBUG)

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Transfer
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

@decorators.elasticsearch_required()
def grid(request):
    try:
        source_directories = storage_service.get_location(purpose="TS")
    except:
        messages.warning(request, 'Error retrieving source directories: is the storage server running? Please contact an administrator.')
    else:
        logging.debug("Source directories found: {}".format(source_directories))
        if not source_directories:
            msg = "No <a href='{source_admin}'>transfer source locations</a> are available. Please contact an administrator.".format(
                source_admin=reverse('components.administration.views.sources'))
            messages.warning(request, mark_safe(msg))

    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    uid = request.user.id
    hide_features = helpers.hidden_features()
    return render(request, 'transfer/grid.html', locals())

def browser(request):
    originals_directory = '/var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog/originals'
    arrange_directory = '/var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog/arrange'
    if not os.path.exists(originals_directory):
        os.mkdir(originals_directory)
    if not os.path.exists(arrange_directory):
        os.mkdir(arrange_directory)
    return render(request, 'transfer/browser.html', locals())

def status(request, uuid=None):
    # Equivalent to: "SELECT SIPUUID, MAX(createdTime) AS latest FROM Jobs GROUP BY SIPUUID
    objects = models.Job.objects.filter(hidden=False, subjobof='', unittype__exact='unitTransfer').values('sipuuid').annotate(timestamp=Max('createdtime')).exclude(sipuuid__icontains = 'None').order_by('-timestamp')
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
            jobs = helpers.get_jobs_by_sipuuid(item['sipuuid'])
            item['directory'] = os.path.basename(utils.get_directory_name_from_job(jobs[0]))
            item['timestamp'] = calendar.timegm(item['timestamp'].timetuple())
            item['uuid'] = item['sipuuid']
            item['id'] = item['sipuuid']
            del item['sipuuid']
            item['jobs'] = []
            for job in jobs:
                newJob = {}
                item['jobs'].append(newJob)
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
    return HttpResponse(json.JSONEncoder(default=encoder).encode(response), mimetype='application/json')

def detail(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = utils.get_directory_name_from_job(jobs[0])
    is_waiting = jobs.filter(currentstep='Awaiting decision').count() > 0
    return render(request, 'transfer/detail.html', locals())

def microservices(request, uuid):
    jobs = models.Job.objects.filter(sipuuid=uuid)
    name = utils.get_directory_name_from_job(jobs[0])
    return render(request, 'transfer/microservices.html', locals())

def delete(request, uuid):
    try:
        transfer = models.Transfer.objects.get(uuid__exact=uuid)
        transfer.hidden = True
        transfer.save()
        response = {'removed': True}
        return helpers.json_response(response)
    except:
        raise Http404


def transfer_metadata_type_id():
    return helpers.get_metadata_type_id_by_description('Transfer')


@decorators.load_jobs  # Adds jobs, name
def transfer_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    metadata = models.DublinCore.objects.filter(
        metadataappliestotype__exact=transfer_metadata_type_id(),
        metadataappliestoidentifier__exact=uuid
    )

    return render(request, 'transfer/metadata_list.html', locals())


def transfer_metadata_edit(request, uuid, id=None):
    if id:
        dc = models.DublinCore.objects.get(pk=id)
    else:
        try:
            dc = models.DublinCore.objects.get(metadataappliestotype__exact=1,
                    metadataappliestoidentifier__exact=uuid)
            return redirect('components.transfer.views.transfer_metadata_edit', uuid, dc.id)
        except ObjectDoesNotExist:
            dc = models.DublinCore(
                metadataappliestotype=transfer_metadata_type_id(),
                metadataappliestoidentifier=uuid
            )

    fields = ['title', 'creator', 'subject', 'description', 'publisher',
              'contributor', 'date', 'type', 'format', 'identifier',
              'source', 'relation', 'language', 'coverage', 'rights']

    if request.method == 'POST':
        form = DublinCoreMetadataForm(request.POST)
        if form.is_valid():
            for item in fields:
                if not item in form.cleaned_data:
                    continue
                setattr(dc, item, form.cleaned_data[item])
            dc.save()
            return redirect('components.transfer.views.transfer_metadata_list', uuid)
    else:
        initial = {}
        for item in fields:
            initial[item] = getattr(dc, item)
        form = DublinCoreMetadataForm(initial=initial)
        jobs = models.Job.objects.filter(sipuuid=uuid, subjobof='')
        name = utils.get_directory_name_from_job(jobs[0])

    return render(request, 'transfer/metadata_edit.html', locals())
