# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
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
import logging

import django.http
from django.shortcuts import render

from components import helpers
from contrib import utils
from main import models

LOGGER = logging.getLogger('archivematica.dashboard')


def detail(request, unit_type, unit_uuid):
    """
    Display detailed information about the unit.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP
    """
    jobs = models.Job.objects.filter(sipuuid=unit_uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs)
    is_waiting = jobs.filter(currentstep=models.Job.STATUS_AWAITING_DECISION).count() > 0
    context = {
        'name': name,
        'is_waiting': is_waiting,
        'uuid': unit_uuid,
        'unit_type': unit_type,
    }
    if unit_type == 'transfer':
        set_uuid = models.Transfer.objects.get(uuid=unit_uuid).transfermetadatasetrow_id
        context['set_uuid'] = set_uuid
    return render(request, unit_type + '/detail.html', context)


def microservices(request, unit_type, unit_uuid):
    """
    Display information about what microservices have run.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP

    """
    jobs = models.Job.objects.filter(sipuuid=unit_uuid, subjobof='')
    name = utils.get_directory_name_from_job(jobs)
    return render(request, unit_type + '/microservices.html', {
        'jobs': jobs,
        'name': name,
        'uuid': unit_uuid,
        'unit_type': unit_type,
    })


def mark_hidden(request, unit_type, unit_uuid):
    """
    Marks the unit as hidden to delete it.

    This endpoint assumes you are already logged in.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP
    """
    if request.method not in ('DELETE',):
        return django.http.HttpResponseNotAllowed(['DELETE'])

    try:
        if unit_type == 'transfer':
            unit_model = models.Transfer
        elif unit_type == 'ingest':
            unit_model = models.SIP
        unit = unit_model.objects.get(uuid=unit_uuid)
        unit.hidden = True
        unit.save()
        response = {'removed': True}
        return helpers.json_response(response)
    except Exception:
        LOGGER.debug('Error setting %s %s to hidden', unit_type, unit_uuid, exc_info=True)
        raise django.http.Http404
