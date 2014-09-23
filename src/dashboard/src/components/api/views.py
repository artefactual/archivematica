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

# stdlib, alphabetical
import base64
import json
import shutil
import logging
import os

# Core Django, alphabetical
from django.db.models import Q
import django.http

# External dependencies, alphabetical
from annoying.functions import get_object_or_None
from tastypie.authentication import ApiKeyAuthentication

# This project, alphabetical
from contrib.mcp.client import MCPClient
from components.filesystem_ajax import views as filesystem_ajax_views
from components import helpers
from main import models

LOGGER = logging.getLogger('archivematica.dashboard')
SHARED_DIRECTORY_ROOT = helpers.get_server_config_value('sharedDirectory')


def authenticate_request(request):
    error = None

    api_auth = ApiKeyAuthentication()
    authorized = api_auth.is_authenticated(request)

    if authorized:
        client_ip = request.META['REMOTE_ADDR']
        whitelist = helpers.get_setting('api_whitelist', '127.0.0.1').split()
        # logging.debug('client IP: %s, whitelist: %s', client_ip, whitelist)
        if client_ip not in whitelist:
            error = 'Host/IP ' + client_ip + ' not authorized.'
    else:
        error = 'API key not valid.'

    return error


def get_unit_status(unit_uuid, unit_type):
    """
    Get status for a SIP or Transfer.

    Returns a dict with status info.  Keys will always include 'status' and
    'microservice', and may include 'sip_uuid'.

    Status is one of FAILED, REJECTED, USER_INPUT, COMPLETE or PROCESSING.
    Microservice is the name of the current microservice.
    SIP UUID is populated only if the unit_type was unitTransfer and status is
    COMPLETE.  Otherwise, it is None.

    :param str unit_uuid: UUID of the SIP or Transfer
    :param str unit_type: unitSIP or unitTransfer
    :return: Dict with status info.
    """
    ret = {}
    job = models.Job.objects.filter(sipuuid=unit_uuid).filter(unittype=unit_type).order_by('-createdtime', '-createdtimedec')[0]
    ret['microservice'] = job.jobtype
    if job.currentstep == 'Awaiting decision':
        ret['status'] = 'USER_INPUT'
    elif 'failed' in job.microservicegroup.lower():
        ret['status'] = 'FAILED'
    elif 'reject' in job.microservicegroup.lower():
        ret['status'] = 'REJECTED'
    elif job.jobtype == 'Remove the processing directory':  # Done storing AIP
        ret['status'] = 'COMPLETE'
    elif models.Job.objects.filter(sipuuid=unit_uuid).filter(jobtype='Create SIP from transfer objects').exists():
        ret['status'] = 'COMPLETE'
        # Get SIP UUID
        sips = models.File.objects.filter(transfer_id=unit_uuid, sip__isnull=False).values('sip').distinct()
        if sips:
            ret['sip_uuid'] = sips[0]['sip']
    elif models.Job.objects.filter(sipuuid=unit_uuid).filter(jobtype='Move transfer to backlog').exists():
        ret['status'] = 'COMPLETE'
        ret['sip_uuid'] = 'BACKLOG'
    else:
        ret['status'] = 'PROCESSING'

    return ret


def status(request, unit_uuid, unit_type):
    # Example: http://127.0.0.1/api/transfer/status/?username=mike&api_key=<API key>
    if request.method not in ('GET',):
        return django.http.HttpResponseNotAllowed(['GET'])
    auth_error = authenticate_request(request)
    response = {}
    if auth_error is not None:
        response = {'message': auth_error, 'error': True}
        return django.http.HttpResponseForbidden(
            json.dumps(response),
            content_type='application/json'
        )
    error = None

    # Get info about unit
    if unit_type == 'unitTransfer':
        unit = get_object_or_None(models.Transfer, uuid=unit_uuid)
        response['type'] = 'transfer'
    elif unit_type == 'unitSIP':
        unit = get_object_or_None(models.SIP, uuid=unit_uuid)
        response['type'] = 'SIP'

    if unit is None:
        response['message'] = 'Cannot fetch {} with UUID {}'.format(unit_type, unit_uuid)
        response['error'] = True
        return django.http.HttpResponseBadRequest(
            json.dumps(response),
            content_type='application/json',
        )
    directory = unit.currentpath if unit_type == 'unitSIP' else unit.currentlocation
    response['path'] = directory.replace('%sharedPath%', SHARED_DIRECTORY_ROOT, 1)
    response['directory'] = os.path.basename(os.path.normpath(directory))
    response['name'] = response['directory'].replace('-' + unit_uuid, '', 1)
    response['uuid'] = unit_uuid

    # Get status (including new SIP uuid, current microservice)
    status_info = get_unit_status(unit_uuid, unit_type)
    response.update(status_info)

    if error is not None:
        response['message'] = error
        response['error'] = True
        return django.http.HttpResponseServerError(
            json.dumps(response),
            content_type='application/json'
        )
    response['message'] = 'Fetched status for {} successfully.'.format(unit_uuid)
    return helpers.json_response(response)


def waiting_for_user_input(request):
    # Example: http://127.0.0.1/api/transfer/waiting?username=mike&api_key=<API key>
    if request.method not in ('GET',):
        return django.http.HttpResponseNotAllowed(['GET'])

    auth_error = authenticate_request(request)
    response = {}
    if auth_error is not None:
        response = {'message': auth_error, 'error': True}
        return django.http.HttpResponseForbidden(
            json.dumps(response),
            content_type='application/json'
        )

    error = None
    waiting_units = []

    jobs = models.Job.objects.filter(currentstep='Awaiting decision')
    for job in jobs:
        unit_uuid = job.sipuuid
        directory = os.path.basename(os.path.normpath(job.directory))
        unit_name = directory.replace('-' + unit_uuid, '', 1)

        waiting_units.append({
            'sip_directory': directory,
            'sip_uuid': unit_uuid,
            'sip_name': unit_name,
            'microservice': job.jobtype,
            # 'choices': []  # TODO? Return list of choices, see ingest.views.ingest_status
        })

    response['results'] = waiting_units

    if error is not None:
        response['message'] = error
        response['error'] = True
        return django.http.HttpResponseServerError(
            json.dumps(response),
            content_type='application/json'
        )
    response['message'] = 'Fetched transfers successfully.'
    return helpers.json_response(response)


def start_transfer_api(request):
    """
    Endpoint for starting a transfer if calling remote and using an API key.
    """
    if request.method not in ('POST',):
        return django.http.HttpResponseNotAllowed(['POST'])

    auth_error = authenticate_request(request)
    response = {}
    if auth_error is not None:
        response = {'message': auth_error, 'error': True}
        return django.http.HttpResponseForbidden(
            json.dumps(response),
            content_type='application/json'
        )

    transfer_name = request.POST.get('name', '')
    transfer_type = request.POST.get('type', '')
    accession = request.POST.get('accession', '')
    # Note that the path may contain arbitrary, non-unicode characters,
    # and hence is POSTed to the server base64-encoded
    paths = request.POST.getlist('paths[]', [])
    paths = [base64.b64decode(path) for path in paths]
    row_ids = request.POST.getlist('row_ids[]', [''])

    response = filesystem_ajax_views.start_transfer(transfer_name, transfer_type, accession, paths, row_ids)
    return helpers.json_response(response)


def unapproved_transfers(request):
    # Example: http://127.0.0.1/api/transfer/unapproved?username=mike&api_key=<API key>
    if request.method == 'GET':
        auth_error = authenticate_request(request)

        response = {}

        if auth_error is None:
            error = None
            unapproved = []

            jobs = models.Job.objects.filter(
                (
                    Q(jobtype="Approve standard transfer")
                    | Q(jobtype="Approve DSpace transfer")
                    | Q(jobtype="Approve bagit transfer")
                    | Q(jobtype="Approve zipped bagit transfer")
                ) & Q(currentstep='Awaiting decision')
            )

            for job in jobs:
                # remove standard transfer path from directory (and last character)
                type_and_directory = job.directory.replace(
                    get_modified_standard_transfer_path() + '/',
                    '',
                    1
                )

                # remove trailing slash if not a zipped bag file
                if not helpers.file_is_an_archive(job.directory):
                    type_and_directory = type_and_directory[:-1]

                transfer_watch_directory = type_and_directory.split('/')[0]
                # Get transfer type from transfer directory
                transfer_type_directories_reversed = {v: k for k, v in filesystem_ajax_views.TRANSFER_TYPE_DIRECTORIES.iteritems()}
                transfer_type = transfer_type_directories_reversed[transfer_watch_directory]

                job_directory = type_and_directory.replace(transfer_watch_directory + '/', '', 1)

                unapproved.append({
                    'type': transfer_type,
                    'directory': job_directory,
                    'uuid': job.sipuuid,
                })

            # get list of unapproved transfers
            # return list as JSON
            response['results'] = unapproved

            if error is not None:
                response['message'] = error
                response['error'] = True
            else:
                response['message'] = 'Fetched unapproved transfers successfully.'

                if error is not None:
                    return helpers.json_response(response, status_code=500)
                else:
                    return helpers.json_response(response)
        else:
            response['message'] = auth_error
            response['error'] = True
            return helpers.json_response(response, status_code=403)
    else:
        return django.http.HttpResponseNotAllowed(permitted_methods=['GET'])

def approve_transfer(request):
    # Example: curl --data \
    #   "username=mike&api_key=<API key>&directory=MyTransfer" \
    #   http://127.0.0.1/api/transfer/approve
    if request.method == 'POST':
        auth_error = authenticate_request(request)

        response = {}

        if auth_error is None:
            error = None

            directory = request.POST.get('directory', '')
            transfer_type = request.POST.get('type', 'standard')
            error, unit_uuid = approve_transfer_via_mcp(directory, transfer_type, request.user.id)

            if error is not None:
                response['message'] = error
                response['error'] = True
                return helpers.json_response(response, status_code=500)
            else:
                response['message'] = 'Approval successful.'
                response['uuid'] = unit_uuid
                return helpers.json_response(response)
        else:
            response['message'] = auth_error
            response['error'] = True
            return helpers.json_response(response, status_code=403)
    else:
        return django.http.HttpResponseNotAllowed(permitted_methods=['POST'])


def get_modified_standard_transfer_path(transfer_type=None):
    path = os.path.join(
        helpers.get_server_config_value('watchDirectoryPath'),
        'activeTransfers'
    )

    if transfer_type is not None:
        try:
            path = os.path.join(path, filesystem_ajax_views.TRANSFER_TYPE_DIRECTORIES[transfer_type])
        except:
            return None

    return path.replace(SHARED_DIRECTORY_ROOT, '%sharedPath%', 1)


def approve_transfer_via_mcp(directory, transfer_type, user_id):
    error = None
    unit_uuid = None
    if (directory != ''):
        # assemble transfer path
        modified_transfer_path = get_modified_standard_transfer_path(transfer_type)

        if modified_transfer_path is None:
            error = 'Invalid transfer type.'
        else:
            db_transfer_path = os.path.join(modified_transfer_path, directory)
            transfer_path = db_transfer_path.replace('%sharedPath%', SHARED_DIRECTORY_ROOT, 1)
            # Ensure directories end with /
            if os.path.isdir(transfer_path):
                db_transfer_path = os.path.join(db_transfer_path, '')
            # look up job UUID using transfer path
            try:
                job = models.Job.objects.filter(directory=db_transfer_path, currentstep='Awaiting decision')[0]
                unit_uuid = job.sipuuid

                type_task_config_descriptions = {
                    'standard': 'Approve standard transfer',
                    'unzipped bag': 'Approve bagit transfer',
                    'zipped bag': 'Approve zipped bagit transfer',
                    'dspace': 'Approve DSpace transfer',
                    'maildir': 'Approve maildir transfer',
                    'TRIM': 'Approve TRIM transfer'
                }

                type_description = type_task_config_descriptions[transfer_type]

                # use transfer type to fetch possible choices to execute
                choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink__currenttask__description=type_description)

                # attempt to find appropriate choice
                chain_to_execute = None
                for choice in choices:
                    if choice.chainavailable.description == 'Approve transfer':
                        chain_to_execute = choice.chainavailable.pk

                # execute choice if found
                if chain_to_execute is not None:
                    client = MCPClient()
                    client.execute(job.pk, chain_to_execute, user_id)
                else:
                    error = 'Error: could not find MCP choice to execute.'

            except Exception:
                error = 'Unable to find unapproved transfer directory.'
                # logging.exception(error)

    else:
        error = 'Please specify a transfer directory.'

    return error, unit_uuid

def start_reingest(request):
    """
    Endpoint to approve reingest of an AIP.

    Expects a POST request with the `uuid` of the SIP, and the `name`, which is
    also the directory in %sharedPath%tmp where the SIP is found.

    Example usage: curl --data "username=demo&api_key=<API key>&name=test-efeb95b4-5e44-45a4-ab5a-9d700875eb60&uuid=efeb95b4-5e44-45a4-ab5a-9d700875eb60"  http://localhost/api/ingest/reingest
    """
    if request.method == 'POST':
        error = authenticate_request(request)
        if error:
            response = {'error': True, 'message': error}
            return helpers.json_response(response, status_code=403)
        sip_name = request.POST.get('name')
        sip_uuid = request.POST.get('uuid')
        if not all([sip_name, sip_uuid]):
            response = {'error': True, 'message': '"name" and "uuid" are required.'}
            return helpers.json_response(response, status_code=400)
        # TODO Clear DB of residual stuff related to SIP
        models.Task.objects.filter(job__sipuuid=sip_uuid).delete()
        models.Job.objects.filter(sipuuid=sip_uuid).delete()
        models.SIP.objects.filter(uuid=sip_uuid).delete()  # Delete is cascading

        # Move to watched directory
        shared_directory_path = helpers.get_server_config_value('sharedDirectory')
        source = os.path.join(shared_directory_path, 'tmp', sip_name)
        dest = os.path.join(shared_directory_path, 'watchedDirectories', 'system', 'reingestAIP', '')
        try:
            LOGGER.debug('Reingest moving from %s to %s', source, dest)
            shutil.move(source, dest)
        except (shutil.Error, OSError) as e:
            error = e.strerror or "Unable to move reingested AIP to start reingest."
            LOGGER.warning('Unable to move reingested AIP to start reingest', exc_info=True)
        if error:
            response = {'error': True, 'message': error}
            return helpers.json_response(response, status_code=500)
        else:
            response = {'message': 'Approval successful.'}
            return helpers.json_response(response)
    else:
        return django.http.HttpResponseNotAllowed(permitted_methods=['POST'])


def get_levels_of_description(request):
    """
    Returns a JSON-encoded set of the configured levels of description.

    The response is an array of objects containing the UUID and name for
    each level of description.
    """
    levels = models.LevelOfDescription.objects.all().order_by('sortorder')
    response = [{l.id: l.name} for l in levels]
    return helpers.json_response(response)

def fetch_levels_of_description_from_atom(request):
    """
    Fetch all levels of description from an AtoM database, removing
    all levels of description already contained there.

    Returns the newly-populated set of levels of descriptions as JSON.

    On error, returns 500 with an error message. This typically occurs if
    AtoM was unable to return a set of levels of description.
    """
    try:
        helpers.get_atom_levels_of_description(clear=True)
    except Exception as e:
        message = str(e)
        body = {
            "success": False,
            "error": message
        }
        return helpers.json_response(body, status_code=500)
    else:
        return get_levels_of_description(request)

def path_metadata(request):
    """
    Fetch metadata for a path (HTTP GET) or add/update it (HTTP POST).

    GET returns a dict of metadata (currently only level of description).
    """

    # Determine path being requested/updated
    path = request.GET.get('path', '') if request.method == 'GET' else request.POST.get('path', '')

    # Get current metadata, if any
    file_lod = get_object_or_None(models.SIPArrange, arrange_path=path, sip_created=False)
    if file_lod is None:
        # Try with trailing / to see if it's a directory
        file_lod = get_object_or_None(models.SIPArrange, arrange_path=path+'/', sip_created=False)

    # Return current metadata, if requested
    if request.method == 'GET':
        level_of_description = file_lod.level_of_description if file_lod is not None else ''

        return helpers.json_response({
            "level_of_description": level_of_description
        })

    # Add/update metadata, if requested
    if request.method == 'POST':
        level_of_description_id = request.POST.get('level_of_description', '')

        level_of_description = get_object_or_None(models.LevelOfDescription, id=level_of_description_id)

        file_lod.relative_location = path
        file_lod.level_of_description = level_of_description.name if level_of_description is not None else ''
        file_lod.save()

        body = {
            "success": True,
        }

        return helpers.json_response(body, status_code=201)
