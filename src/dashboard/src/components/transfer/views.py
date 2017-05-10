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

import json
import logging
from uuid import uuid4

from django.db.models import Max
from django.conf import settings as django_settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _

from contrib import utils
from components import helpers
from components.ingest.forms import DublinCoreMetadataForm
import components.decorators as decorators
from main import models

import storageService as storage_service

logger = logging.getLogger('archivematica.dashboard')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Transfer
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def grid(request):
    polling_interval = django_settings.POLLING_INTERVAL
    microservices_help = django_settings.MICROSERVICES_HELP
    uid = request.user.id
    return render(request, 'transfer/grid.html', locals())

def transfer_source_locations(request):
    try:
        return helpers.json_response(storage_service.get_location(purpose="TS"))
    except:
        message = _('Error retrieving source directories')
        logger.exception(message)
        response = {
            'message': message,
            'status': 'Failure',
        }
        return helpers.json_response(response, status_code=500)

def component(request, uuid):
    messages = []
    fields_saved = False

    # get set/field data and initialize dict of form field values
    metadata_set, created = models.TransferMetadataSet.objects.get_or_create(
        pk=uuid, defaults={'createdbyuserid': request.user.id}
    )
    if created:
        metadata_set.save()
    fields = models.TransferMetadataField.objects.all().order_by('sortorder')
    values = {}  # field values
    options = [] # field options (for value selection)

    for field in fields:
        if field.optiontaxonomy is not None:
            # check for newly added terms
            new_term = request.POST.get('add_to_' + field.pk, '')
            if new_term != '':
                term = models.TaxonomyTerm()
                term.taxonomy = field.optiontaxonomy
                term.term = new_term
                term.save()
                messages.append('Term added.')

            # load taxonomy terms into option values
            optionvalues = ['']
            for term in field.optiontaxonomy.taxonomyterm_set.iterator():
                optionvalues.append(term.term)
            options.append({
                'field':   field,
                'options': optionvalues
            })

            # determine whether field should allow new terms to be specified
            field.allownewvalue = True
            # support allownewvalue
            # by loading taxonomy and checked if it's open
        try:
            field_value = models.TransferMetadataFieldValue.objects.get(
                field=field,
                set=metadata_set
            )
            values[(field.fieldname)] = field_value.fieldvalue
        except models.TransferMetadataFieldValue.DoesNotExist:
            if request.method == 'POST':
                field_value = models.TransferMetadataFieldValue()
                field_value.field = field
                field_value.set = metadata_set
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


def status(request, uuid=None):
    # Equivalent to: "SELECT SIPUUID, MAX(createdTime) AS latest FROM Jobs GROUP BY SIPUUID
    objects = models.Job.objects.filter(hidden=False, subjobof='', unittype__exact='unitTransfer').values('sipuuid').annotate(timestamp=Max('createdtime')).exclude(sipuuid__icontains = 'None').order_by('-timestamp')
    status = helpers.units_status(request, objects, unit_type='transfer')
    return helpers.json_response(status)


def transfer_metadata_type_id():
    return helpers.get_metadata_type_id_by_description('Transfer')


@decorators.load_jobs  # Adds jobs, name
def transfer_metadata_list(request, uuid, jobs, name):
    # See MetadataAppliesToTypes table
    metadata = models.DublinCore.objects.filter(
        metadataappliestotype=transfer_metadata_type_id(),
        metadataappliestoidentifier__exact=uuid
    )

    return render(request, 'transfer/metadata_list.html', locals())


def transfer_metadata_edit(request, uuid, id=None):
    if id:
        dc = models.DublinCore.objects.get(pk=id)
    else:
        try:
            dc = models.DublinCore.objects.get(metadataappliestotype=transfer_metadata_type_id(), metadataappliestoidentifier__exact=uuid)
            return redirect('components.transfer.views.transfer_metadata_edit', uuid, dc.id)
        except models.DublinCore.DoesNotExist:
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
        name = utils.get_directory_name_from_job(jobs)

    return render(request, 'transfer/metadata_edit.html', locals())

def create_metadata_set_uuid(request):
    """
    Transfer metadata sets are used to associate a group of metadata field values with
    a transfer. The transfer metadata set UUID is relayed to the MCP chain by including
    it in a row in a pre-created Transfers table entry.
    """
    response = {}
    response['uuid'] = str(uuid4())

    return HttpResponse(
        json.dumps(response),
        content_type='application/json'
    )

def rename_metadata_set(request, set_uuid, placeholder_id):
    response = {}

    try:
        path = request.POST['path']
        fields = models.TransferMetadataFieldValue.objects.filter(set_id=set_uuid, filepath=placeholder_id)
        fields.update(filepath=path)
        response['status'] = 'Success'
    except KeyError:
        response['status'] = 'Failure'
        response['message'] = _('Updated path was not provided.')
    except Exception as e:
        if not e.message:
            message = _('Unable to update transfer metadata set: contact administrator.')
        else:
            message = e.message
        response['status'] = 'Failure'
        response['message'] = message

    return HttpResponse(
        json.dumps(response),
        content_type='application/json'
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
        objects = models.TransferMetadataFieldValue.objects.filter(set_id=set_uuid)
        response['deleted_objects'] = len(objects)
        objects.delete()
        models.TransferMetadataSet.objects.get(id=set_uuid).delete()
    except Exception as e:
        response['message'] = e.message

    return HttpResponse(
        json.dumps(response),
        content_type='application/json'
    )
