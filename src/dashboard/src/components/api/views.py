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
import uuid
import re

# Core Django, alphabetical
from django.db.models import Q
import django.http
from django.conf import settings as django_settings

# External dependencies, alphabetical
from annoying.functions import get_object_or_None
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication

# This project, alphabetical
import archivematicaFunctions
from contrib.mcp.client import MCPClient
from components.filesystem_ajax import views as filesystem_ajax_views
from components.unit import views as unit_views
from components import helpers
from main import models
from processing import install_builtin_config

LOGGER = logging.getLogger('archivematica.dashboard')
SHARED_DIRECTORY_ROOT = django_settings.SHARED_DIRECTORY
UUID_REGEX = re.compile(r'^[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}$', re.IGNORECASE)


def _api_endpoint(expected_methods):
    """
    Decorator for authenticated API calls that handles boilerplate code.

    Checks if method is allowed, and request is authenticated.
    """
    def decorator(func):
        """The decorator applied to the endpoint."""
        def wrapper(request, *args, **kwargs):
            """Wrapper for custom endpoints with boilerplate code."""
            # Check HTTP verb
            if request.method not in expected_methods:
                return django.http.HttpResponseNotAllowed(expected_methods)  # 405

            # Auth
            auth_error = authenticate_request(request)
            if auth_error is not None:
                response = {'message': auth_error, 'error': True}
                return django.http.HttpResponseForbidden(  # 403
                    json.dumps(response),
                    content_type='application/json'
                )

            # Call the decorated method
            result = func(request, *args, **kwargs)

            return result
        return wrapper
    return decorator


def allowed_by_whitelist(ip_address):
    whitelist = [
        ip.strip()
        for ip in helpers.get_setting('api_whitelist', '').split()
    ]

    # If there's no whitelist, allow all through
    if not whitelist:
        return True

    LOGGER.debug('looking for ip %s in whitelist %s', ip_address, whitelist)
    # There is a whitelist - check the IP address against it
    if ip_address in whitelist:
        LOGGER.debug('API called by trusted IP %s', ip_address)
        return True

    return False


def authenticate_request(request):
    error = None
    client_ip = request.META['REMOTE_ADDR']
    whitelist = helpers.get_setting('api_whitelist', '').split()
    if client_ip in whitelist:
        LOGGER.debug('API called by trusted IP %s', client_ip)
        return None

    api_auth = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
    authorized = api_auth.is_authenticated(request)

    # 'authorized' can be True, False or tastypie.http.HttpUnauthorized
    # Check explicitly for True, not just truthiness
    if authorized is not True:
        error = 'API key not valid.'

    elif not allowed_by_whitelist(client_ip):
        error = 'Host/IP ' + client_ip + ' not authorized.'

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
    if job.currentstep == models.Job.STATUS_AWAITING_DECISION:
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


@_api_endpoint(expected_methods=['GET'])
def status(request, unit_uuid, unit_type):
    # Example: http://127.0.0.1/api/transfer/status/?username=mike&api_key=<API key>
    response = {}
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
        return django.http.HttpResponseBadRequest(  # 400
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
        return django.http.HttpResponseServerError(  # 500
            json.dumps(response),
            content_type='application/json'
        )
    response['message'] = 'Fetched status for {} successfully.'.format(unit_uuid)
    return helpers.json_response(response)


@_api_endpoint(expected_methods=['GET'])
def waiting_for_user_input(request):
    # Example: http://127.0.0.1/api/ingest/waiting?username=mike&api_key=<API key>
    response = {}
    waiting_units = []

    # TODO should this filter based on unit type into transfer vs SIP?
    jobs = models.Job.objects.filter(currentstep=models.Job.STATUS_AWAITING_DECISION)
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
    response['message'] = 'Fetched units successfully.'
    return helpers.json_response(response)


@_api_endpoint(expected_methods=['DELETE'])
def mark_hidden(request, unit_type, unit_uuid):
    """
    Mark a unit as deleted and hide it in the dashboard.

    This is just a wrapper around unit.views.mark_hidden that verifies API auth.

    :param unit_type: 'transfer' or 'ingest' for a Transfer or SIP respectively
    :param unit_uuid: UUID of the Transfer or SIP
    """
    return unit_views.mark_hidden(request, unit_type, unit_uuid)


@_api_endpoint(expected_methods=['DELETE'])
def mark_completed_hidden(request, unit_type):
    """Mark all completed (``unit_type``) units as deleted.

    This is just a wrapper around unit.views.mark_completed_hidden that
    verifies API auth.

    :param unit_type: 'transfer' or 'ingest' for Transfers or SIPs, respectively

    Usage::

        $ curl -X DELETE \
               -H"Authorization: ApiKey test:5c2f6c8fbaff3b3038f89ab05b1c2267e447581e" \
               'http://localhost/api/transfer/delete/'
    """
    return unit_views.mark_completed_hidden(request, unit_type)


@_api_endpoint(expected_methods=['POST'])
def start_transfer_api(request):
    """
    Endpoint for starting a transfer if calling remote and using an API key.
    """
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


@_api_endpoint(expected_methods=['GET'])
def completed_transfers(request):
    """Return all completed transfers::

        GET /api/transfer/completed?username=<am-username>&api_key=<am-api-key>

    """
    response = {}
    completed = _completed_units(unit_type='transfer')
    response['results'] = completed
    response['message'] = 'Fetched completed transfers successfully.'
    return helpers.json_response(response)


@_api_endpoint(expected_methods=['GET'])
def completed_ingests(request):
    """Return all completed ingests::

        GET /api/ingest/completed?username=<am-username>&api_key=<am-api-key>

    """
    response = {}
    completed = _completed_units(unit_type='ingest')
    response['results'] = completed
    response['message'] = 'Fetched completed ingests successfully.'
    return helpers.json_response(response)


def _completed_units(unit_type='transfer'):
    """Return all completed units of type `unit_type`, one of 'transfer' or
    'ingest'.
    """
    model_name = {'transfer': 'Transfer', 'ingest': 'SIP'}.get(unit_type)
    model = getattr(models, model_name)
    completed = []
    units = model.objects.filter(hidden=False)
    for unit in units:
        status = get_unit_status(unit.uuid, 'unit{0}'.format(model_name))
        if status.get('status') == 'COMPLETE':
            completed.append(unit.uuid)
    return completed


@_api_endpoint(expected_methods=['GET'])
def unapproved_transfers(request):
    # Example: http://127.0.0.1/api/transfer/unapproved?username=mike&api_key=<API key>
    response = {}
    unapproved = []

    jobs = models.Job.objects.filter(
        (
            Q(jobtype="Approve standard transfer") | Q(jobtype="Approve DSpace transfer") | Q(jobtype="Approve bagit transfer") | Q(jobtype="Approve zipped bagit transfer")
        ) & Q(currentstep=models.Job.STATUS_AWAITING_DECISION)
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
        transfer_type_directories_reversed = {v: k for k, v in filesystem_ajax_views.TRANSFER_TYPE_DIRECTORIES.items()}
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
    response['message'] = 'Fetched unapproved transfers successfully.'
    return helpers.json_response(response)


@_api_endpoint(expected_methods=['POST'])
def approve_transfer(request):
    # Example: curl --data \
    #   "username=mike&api_key=<API key>&directory=MyTransfer" \
    #   http://127.0.0.1/api/transfer/approve
    response = {}
    error = None

    directory = request.POST.get('directory', '')
    transfer_type = request.POST.get('type', 'standard')
    directory = archivematicaFunctions.unicodeToStr(directory)
    error, unit_uuid = approve_transfer_via_mcp(directory, transfer_type, request.user.id)

    if error is not None:
        response['message'] = error
        response['error'] = True
        return helpers.json_response(response, status_code=500)
    else:
        response['message'] = 'Approval successful.'
        response['uuid'] = unit_uuid
        return helpers.json_response(response)


def get_modified_standard_transfer_path(transfer_type=None):
    path = os.path.join(
        django_settings.WATCH_DIRECTORY,
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
                job = models.Job.objects.filter(directory=db_transfer_path, currentstep=models.Job.STATUS_AWAITING_DECISION)[0]
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


@_api_endpoint(expected_methods=['POST'])
def reingest_approve(request):
    """Approve an AIP partial re-ingest.

    - Method:      POST
    - URL:         api/ingest/reingest/approve
    - POST params:
                   - username -- AM username
                   - api_key  -- AM API key
                   - uuid     -- SIP UUID

    TODO: this is just a temporary way of getting the API to do the
    equivalent of clicking "Approve AIP reingest" in the dashboard when faced
    with "Approve AIP reingest". This is non-dry given
    ``approve_transfer_via_mcp`` above and should probably me made congruent
    with that function and ``approve_transfer``.
    """
    sip_uuid = request.POST.get('uuid')
    if sip_uuid is None:
        response = {'error': True, 'message': '"uuid" is required.'}
        return helpers.json_response(response, status_code=400)
    job = models.Job.objects.filter(
        sipuuid=sip_uuid,
        microservicegroup='Reingest AIP',
        currentstep=models.Job.STATUS_AWAITING_DECISION
    ).first()
    if job:
        chain = models.MicroServiceChainChoice.objects.filter(
            choiceavailableatlink__currenttask__description='Approve AIP reingest',
            chainavailable__description='Approve AIP reingest'
        ).first()

        if chain:
            approve_aip_reingest_choice_uuid = chain.chainavailable.pk
            client = MCPClient()
            client.execute(job.pk, approve_aip_reingest_choice_uuid, request.user.id)

            response = {'message': 'Approval successful.'}
        else:
            # No choice was found.
            response = {
                'error': True,
                'message': 'Could not find choice for approve AIP reingest'
            }
            return helpers.json_response(response, status_code=400)

        return helpers.json_response(response)
    else:
        # No job to be found.
        response = {'error': True,
                    'message': ('There is no "Reingest AIP" job awaiting a'
                                ' decision for SIP {}'.format(sip_uuid))}
        return helpers.json_response(response, status_code=400)


@_api_endpoint(expected_methods=['POST'])
def reingest(request, target):
    """
    Endpoint to approve reingest of an AIP to the beginning of transfer or ingest.

    Expects a POST request with the `uuid` of the SIP, and the `name`, which is
    also the directory in %sharedPath%tmp where the SIP is found.

    Example usage:

        $ http POST http://localhost/api/ingest/reingest \
          username=demo api_key=$API_KEY \
          name=test-efeb95b4-5e44-45a4-ab5a-9d700875eb60 \
          uuid=efeb95b4-5e44-45a4-ab5a-9d700875eb60

    :param str target: ingest or transfer
    """
    error = None
    sip_name = request.POST.get('name')
    sip_uuid = request.POST.get('uuid')
    if not all([sip_name, sip_uuid]):
        response = {'error': True, 'message': '"name" and "uuid" are required.'}
        return helpers.json_response(response, status_code=400)
    if target not in ('transfer', 'ingest'):
        response = {'error': True, 'message': 'Unknown tranfer type.'}
        return helpers.json_response(response, status_code=400)

    # TODO Clear DB of residual stuff related to SIP
    models.Task.objects.filter(job__sipuuid=sip_uuid).delete()
    models.Job.objects.filter(sipuuid=sip_uuid).delete()
    models.SIP.objects.filter(uuid=sip_uuid).delete()  # Delete is cascading
    models.RightsStatement.objects.filter(metadataappliestoidentifier=sip_uuid).delete()  # Not actually a foreign key
    models.DublinCore.objects.filter(metadataappliestoidentifier=sip_uuid).delete()

    shared_directory_path = django_settings.SHARED_DIRECTORY
    source = os.path.join(shared_directory_path, 'tmp', sip_name)

    reingest_uuid = sip_uuid
    if target == 'transfer':
        dest = os.path.join(shared_directory_path, 'watchedDirectories', 'activeTransfers', 'standardTransfer')
        # If the destination dir has a UUID, remove it
        sip_basename = os.path.basename(os.path.normpath(sip_name))
        name_has_uuid = len(sip_basename) > 36 and re.match(UUID_REGEX, sip_basename[-36:]) is not None
        if name_has_uuid:
            dest = os.path.join(dest, sip_basename[:-37])
            if os.path.isdir(dest):
                response = {'error': True, 'message': 'There is already a transfer in standardTransfer with the same name.'}
                return helpers.json_response(response, status_code=400)
        dest = os.path.join(dest, '')

        # Persist transfer record in the database
        tdetails = {
            'currentlocation': '%sharedPath%' + dest[len(shared_directory_path):],
            'uuid': str(uuid.uuid4()),
            'type': 'Archivematica AIP',
        }
        reingest_uuid = tdetails['uuid']
        models.Transfer.objects.create(**tdetails)
        LOGGER.info('Transfer saved in the database (uuid=%s, type=%s, location=%s)', tdetails['uuid'], tdetails['type'], tdetails['currentlocation'])

    elif target == 'ingest':
        dest = os.path.join(shared_directory_path, 'watchedDirectories', 'system', 'reingestAIP', '')

    # Move to watched directory
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
        response = {'message': 'Approval successful.', 'reingest_uuid': reingest_uuid}
        return helpers.json_response(response)

# TODO should this have auth?  Does it support GET?


@_api_endpoint(expected_methods=['POST'])
def copy_metadata_files_api(request):
    """
    Endpoint for adding metadata files to a SIP if using an API key.
    """
    sip_uuid = request.POST.get('sip_uuid')
    paths = request.POST.getlist('source_paths[]')
    return filesystem_ajax_views.copy_metadata_files(sip_uuid, paths)

# TODO should this have auth?


@_api_endpoint(expected_methods=['GET'])
def get_levels_of_description(request):
    """
    Returns a JSON-encoded set of the configured levels of description.

    The response is an array of objects containing the UUID and name for
    each level of description.
    """
    levels = models.LevelOfDescription.objects.all().order_by('sortorder')
    response = [{l.id: l.name} for l in levels]
    return helpers.json_response(response)

# TODO should this have auth?


@_api_endpoint(expected_methods=['GET'])
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

# TODO should this have auth?


@_api_endpoint(expected_methods=['GET', 'POST'])
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
        file_lod = get_object_or_None(models.SIPArrange, arrange_path=path + '/', sip_created=False)

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


# TODO should this have auth?
@_api_endpoint(expected_methods=['GET', 'DELETE'])
def processing_configuration(request, name):
    """
    Return a processing configuration XML document given its name, i.e. where
    name is "default" the returned file will be "defaultProcessingMCP.xml"
    found in the standard processing configuration directory.
    """

    config_path = os.path.join(helpers.processing_config_path(), '{}ProcessingMCP.xml'.format(name))

    if request.method == 'DELETE':
        try:
            os.remove(config_path)
            return helpers.json_response({'success': True})
        except OSError:
            msg = 'No such processing config "%s".' % name
            LOGGER.error(msg)
            return helpers.json_response({
                "success": False,
                "error": msg
            }, status_code=404)
    else:
        accepted_types = request.META.get('HTTP_ACCEPT', '').lower()
        if accepted_types != '*/*' and 'xml' not in accepted_types:
            return django.http.HttpResponse(status=415)

        try:
            # Attempt to read the file
            with open(config_path, 'r') as f:
                content = f.read()
        except IOError:
            # The file didn't exist, so recreate it from the builtin config
            try:
                content = install_builtin_config(name)
                if content:
                    LOGGER.info('Regenerated processing config "%s".' % name)
                else:
                    msg = 'No such processing config "%s".' % name
                    LOGGER.error(msg)
                    return helpers.json_response({
                        "success": False,
                        "error": msg
                    }, status_code=404)
            except Exception:
                msg = 'Failed to reset processing config "%s".' % name
                LOGGER.exception(msg)
                return helpers.json_response({
                    "success": False,
                    "error": msg
                }, status_code=500)

        return django.http.HttpResponse(content, content_type='text/xml')
