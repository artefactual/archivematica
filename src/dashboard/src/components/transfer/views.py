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
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.utils.safestring import mark_safe

from contrib.mcp.client import MCPClient
from contrib import utils

from main import models
from components import helpers
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

def component(request, uuid):
    messages = []
    fields_saved = False

    # get set/field data and initialize dict of form field values
    set    = models.TransferMetadataSet.objects.get(pk=uuid)
    fields = models.TransferMetadataField.objects.all().order_by('sortorder')
    values = {}  # field values
    options = [] # field options (for value selection)

    for field in fields:
        if field.optiontaxonomyuuid != '' and field.optiontaxonomyuuid != None:
            # check for newly added terms
            new_term = request.POST.get('add_to_' + field.pk, '')
            if new_term != '':
                term = models.TaxonomyTerm()
                term.taxonomyuuid = field.optiontaxonomyuuid
                term.term = new_term
                term.save()
                messages.append('Term added.')

            # load taxonomy terms into option values
            optionvalues = ['']
            for term in models.TaxonomyTerm.objects.filter(taxonomyuuid=field.optiontaxonomyuuid):
                optionvalues.append(term.term)
            options.append({
                'field':   field.pk,
                'options': optionvalues
            })

            # determine whether field should allow new terms to be specified
            field.allownewvalue = True
            # support allownewvalue
            # by loading taxonomy and checked if it's open
        try:
            field_value = models.TransferMetadataFieldValue.objects.get(
                fielduuid=field.pk,
                setuuid=set.pk
            )
            values[(field.fieldname)] = field_value.fieldvalue
        except:
            if request.method == 'POST':
                field_value = models.TransferMetadataFieldValue()
                field_value.fielduuid = field.pk
                field_value.setuuid = set.pk
            else:
                values[(field.fieldname)] = ''
        if request.method == 'POST':
            field_value.fieldvalue = request.POST.get(field.fieldname, '')
            field_value.save()
            fields_saved = True
            values[(field.fieldname)] = field_value.fieldvalue # override initially loaded value, if any

    if fields_saved:
        messages.append('Metadata saved.')

    return render(request, 'transfer/component.html', locals())

def browser(request):
    originals_directory = '/var/archivematica/sharedDirectory/transferBackups/originals'
    arrange_directory = '/var/archivematica/sharedDirectory/transferBackups/arrange'
    if not os.path.exists(originals_directory):
        os.mkdir(directory)
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
    set_uuid = models.Transfer.objects.get(uuid=uuid).transfermetadatasetrowuuid
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

def create_metadata_set_uuid(request):
    """
    Transfer metadata sets are used to associate a group of metadata field values with
    a transfer. The transfer metadata set UUID is relayed to the MCP chain by including
    it in a row in a pre-created Transfers table entry.
    """
    response = {}

    try:
        ts = models.TransferMetadataSet()
        ts.createdbyuserid = request.user.id
        ts.save()
        response['uuid'] = ts.pk
    except:
        response['message'] = 'Unable to create transfer metadata set: contact administrator.'

    return HttpResponse(
        json.dumps(response),
        mimetype='application/json'
    )

def rename_metadata_set(request, set_uuid, placeholder_id):
    response = {}

    try:
        path = request.POST.get('path')
        if not path:
            raise KeyError
        fields = models.TransferMetadataFieldValue.objects.filter(setuuid=set_uuid, filepath=placeholder_id)
        fields.update(filepath=path)
        response['status'] = 'Success'
    except KeyError:
        response['status'] = 'Failure'
        response['message'] = 'Updated path was not provided.'
    except Exception as e:
        if not e.message:
            message = 'Unable to update transfer metadata set: contact administrator.'
        else:
            message = e.message
        response['status'] = 'Failure'
        response['message'] = message

    return HttpResponse(
        json.dumps(response),
        mimetype='application/json'
    )

def cleanup_metadata_set(request, set_uuid):
    """
    Cleans up any unassigned metadata forms for the given set_uuid.
    Normally these are created with placeholder IDs, then asssigned the
    permanent path within the component after a component is added.
    However, if the user enters a metadata form and then starts the
    transfer without adding a new component, this placeholder form
    needs to be cleaned up before starting the transfer.
    """
    response = {}

    try:
        objects = models.TransferMetadataFieldValue.objects.filter(setuuid=set_uuid)
        response['deleted_objects'] = len(objects)
        objects.delete()
        models.TransferMetadataSet.objects.get(id=set_uuid).delete()
    except Exception as e:
        response['message'] = e.message

    return HttpResponse(
        json.dumps(response),
        mimetype='application/json'
    )
