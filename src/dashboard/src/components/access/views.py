# Standard library, alphabetical by import source
import base64
from functools import wraps
import json
import logging
import os
import uuid

# Django Core, alphabetical by import source
import django.http
from django.shortcuts import redirect

# External dependencies, alphabetical
import MySQLdb  # for ATK exceptions
from agentarchives.archivists_toolkit import ArchivistsToolkitError
from agentarchives.archivesspace import ArchivesSpaceError, AuthenticationError

# This project, alphabetical by import source
from components import helpers
from components.ingest.views_atk import get_atk_system_client
from components.ingest.views_as import get_as_system_client
import components.filesystem_ajax.views as filesystem_views
from main.models import SIP, SIPArrange, SIPArrangeAccessMapping, ArchivesSpaceDOComponent

logger = logging.getLogger('archivematica.dashboard')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Access
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def _get_client_by_type(system):
    if system == "archivesspace":
        return get_as_system_client()
    elif system == "atk":
        return get_atk_system_client()
    else:
        raise ValueError("Unrecognized access system: {}".format(system))


def _authenticate_to_archivesspace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            system = kwargs['system']
            # append the client onto the positional argument list
            client = _get_client_by_type(system)
        except AuthenticationError:
            response = {
                "success": False,
                "message": "Unable to authenticate to ArchivesSpace server using the default user! Check administrative settings."
            }
            return django.http.HttpResponseServerError(json.dumps(response),
                                                       content_type="application/json")
        except ArchivesSpaceError:
            response = {
                "success": False,
                "message": "Unable to connect to ArchivesSpace server at the default location! Check administrative settings."
            }
            return django.http.HttpResponseServerError(json.dumps(response),
                                                       content_type="application/json")
        except (MySQLdb.ProgrammingError, MySQLdb.OperationalError) as e:
            response = {
                "success": False,
                "message": "Unable to connect to Archivist's Toolkit database; failed with error: {}".format(e),
            }
            return django.http.HttpResponseServerError(json.dumps(response),
                                                       content_type="application/json")

        return func(client, *args, **kwargs)
    return wrapper


def _normalize_record_id(record_id):
    """
    Normalizes a record ID that has been mangled for a URL.

    ArchivesSpace record IDs are URL fragments, in the format /repository/n/type/n.
    The slashes are replaced by dashes so that they can be conveniently passed in URLs within this module;
    this function transforms them back into the original format.
    """
    return record_id.replace('-', '/')

def _get_arrange_path(func):
    @wraps(func)
    def wrapper(request, system='', record_id=''):
        try:
            mapping = SIPArrangeAccessMapping.objects.get(system=system, identifier=_normalize_record_id(record_id))
            return func(request, mapping)
        except SIPArrangeAccessMapping.DoesNotExist:
            response = {
                'success': False,
                'message': 'No SIP Arrange mapping exists for record {}'.format(record_id),
            }
            return helpers.json_response(response, status_code=404)
    return wrapper


def _get_or_create_arrange_path(func):
    @wraps(func)
    def wrapper(request, system='', record_id=''):
        mapping = create_arranged_directory(system, record_id)
        return func(request, mapping)
    return wrapper


def _get_sip(func):
    @wraps(func)
    def wrapper(request, mapping):
        arrange = SIPArrange.objects.get(arrange_path=os.path.join(mapping.arrange_path, ''))
        if arrange.sip is None:
            arrange.sip = SIP.objects.create(uuid=(uuid.uuid4()), currentlocation=None)
            arrange.save()
        return func(request, arrange.sip)
    return wrapper


@_authenticate_to_archivesspace
def all_records(client, request, system=''):
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 30)
    search_pattern = request.GET.get('title', '')
    identifier = request.GET.get('identifier', '')

    records = client.find_collections(
        search_pattern=search_pattern,
        identifier=identifier,
        page=page,
        page_size=page_size,
    )

    for i, r in enumerate(records):
        records[i] = _get_sip_arrange_children(r, system)

    return helpers.json_response(records)


@_authenticate_to_archivesspace
def record(client, request, system='', record_id=''):
    if request.method == 'PUT':
        try:
            new_record = json.load(request)
        except ValueError:
            response = {
                'success': False,
                'message': 'No JSON object could be decoded from request body.',
            }
            return helpers.json_response(response, status_code=400)

        try:
            client.edit_record(new_record)
        except (ArchivesSpaceError, ArchivistsToolkitError) as e:
            return helpers.json_response({
                'sucess': False,
                'message': str(e),
            }, status_code=500)
        return helpers.json_response({
            'success': True,
            'message': 'Record updated.',
        })
    elif request.method == 'GET':
        record_id = _normalize_record_id(record_id)

        try:
            records = client.get_resource_component_and_children(record_id,
                                                                 recurse_max_level=3)
            return helpers.json_response(records)
        except ArchivesSpaceError as e:
            return helpers.json_response({'success': False, "message": str(e)}, status_code=400)
    elif request.method == 'DELETE':
        # Delete associated SIPArrange entries
        try:
            mapping = SIPArrangeAccessMapping.objects.get(system=system, identifier=_normalize_record_id(record_id))
        except SIPArrangeAccessMapping.DoesNotExist:
            logger.debug('No access mapping for %s', record_id)
        else:
            filesystem_views.delete_arrange(request, filepath=mapping.arrange_path + '/')
        # Delete in Aspace
        return helpers.json_response(client.delete_record(_normalize_record_id(record_id)))


@_authenticate_to_archivesspace
def get_records_by_accession(client, request, system='', accession=''):
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 30)

    try:
        records = client.find_collections_by_accession(accession, page=page, page_size=page_size)
        return helpers.json_response(records)
    except ArchivesSpaceError as e:
        return helpers.json_response({"error": True, "message": str(e)})


@_authenticate_to_archivesspace
def record_children(client, request, system='', record_id=''):
    record_id = _normalize_record_id(record_id)

    if request.method == 'POST':
        new_record_data = json.load(request)
        try:
            notes = new_record_data.get('notes', [])
            note = notes[0] if notes else {}
            new_id = client.add_child(record_id,
                                      title=new_record_data.get('title', ''),
                                      level=new_record_data.get('level', ''),
                                      start_date=new_record_data.get('start_date', ''),
                                      end_date=new_record_data.get('end_date', ''),
                                      date_expression=new_record_data.get('date_expression', ''),
                                      note=note)
        except ArchivesSpaceError as e:
            response = {
                'success': False,
                'message': str(e),
            }
            return helpers.json_response(response, status_code=400)
        except (MySQLdb.ProgrammingError, MySQLdb.OperationalError) as e:
            response = {
                'success': False,
                'message': 'MySQL error encountered while communicating with Archivist\'s Toolkit: ' + str(e),
            }
            return helpers.json_response(response, status_code=400)

        response = {
            'success': True,
            'id': new_id,
            'message': 'New record successfully created',
        }
        return helpers.json_response(response)
    elif request.method == 'GET':
        records = client.get_resource_component_and_children(record_id,
                                                             recurse_max_level=3)
        records = _get_sip_arrange_children(records, system)
        return helpers.json_response(records['children'])


def get_digital_object_component_path(record_id, component_id, system='archivesspace', create=True):
    mapping = create_arranged_directory(system, record_id)
    component_path = os.path.join(mapping.arrange_path, 'digital_object_component_{}'.format(component_id), '')
    if create:
        filesystem_views.create_arrange_directory(component_path)

    return component_path


@_authenticate_to_archivesspace
def digital_object_components(client, request, system='archivesspace', record_id=''):
    """
    List, modify or view the digital object components associated with the record `record_id`.

    GET:
    Returns a list of all digital object components in the database associated with `record_id`.
    These are returned as dictionaries containing the keys `id`, `label`, and `title`.

    POST:
    Creates a new digital object component associated with `record_id`.
    The `label` and `title` of the new object, and the `uuid` of a SIP with which the component should be associated, can be specified by including a JSON document in the request body with values in those keys.

    PUT:
    Updates an existing digital object component, using `title` and `label` values in a JSON document in the request body.
    The `component_id` to the component to edit must be specified in the request body.
    """
    if request.method == 'POST':
        record = json.load(request)
        component = ArchivesSpaceDOComponent.objects.create(
            resourceid=_normalize_record_id(record_id),
            sip_id=record.get('uuid'),
            label=record.get('label', ''),
            title=record.get('title', ''),
        )

        try:
            get_digital_object_component_path(record_id, component.id, system=system, create=True)
        except ValueError as e:
            component.delete()
            response = {
                'success': False,
                'message': str(e),
            }
            return helpers.json_response(response, status_code=400)

        response = {
            'success': True,
            'message': 'Digital object component successfully created',
            'component_id': component.id,
        }
        return helpers.json_response(response)
    elif request.method == 'GET':
        components = list(ArchivesSpaceDOComponent.objects.filter(resourceid=_normalize_record_id(record_id), started=False).values('id', 'resourceid', 'label', 'title'))
        for component in components:
            access_path = get_digital_object_component_path(record_id, component['id'], system=system)
            component['path'] = access_path
            component['type'] = 'digital_object'
        return helpers.json_response(components)
    elif request.method == 'PUT':
        record = json.load(request)
        try:
            component_id = record['component_id']
        except KeyError:
            response = {
                'success': False,
                'message': 'No component_id was specified!'
            }
            return helpers.json_response(response, status_code=400)

        try:
            component = ArchivesSpaceDOComponent.objects.get(id=component_id)
        except ArchivesSpaceDOComponent.DoesNotExist:
            response = {
                'success': False,
                'message': 'No digital object component exists with the specified ID: {}'.format(component_id),
            }
            return helpers.json_response(response, status_code=404)
        else:
            component.label = record.get('label', '')
            component.title = record.get('title', '')
            component.save()
            return django.http.HttpResponse(status=204)


@_authenticate_to_archivesspace
def digital_object_components_files(client, request, system='archivesspace', record_id='', component_id=''):
    access_path = get_digital_object_component_path(record_id, component_id, system=system)
    return filesystem_views.arrange_contents(request, path=access_path + '/')


def _get_sip_arrange_children(record, system):
    """ Recursively check for SIPArrange associations. """
    try:
        mapping = SIPArrangeAccessMapping.objects.get(system=system, identifier=record['id'])
        record['path'] = mapping.arrange_path
        record['children'] = record['children'] or []
        record['has_children'] = True
    except (SIPArrangeAccessMapping.MultipleObjectsReturned, SIPArrangeAccessMapping.DoesNotExist):
        pass
    if record['children']:  # record['children'] may be False
        for i, r in enumerate(record['children']):
            record['children'][i] = _get_sip_arrange_children(r, system)
    return record

@_authenticate_to_archivesspace
def get_levels_of_description(client, request, system=''):
    levels = client.get_levels_of_description()
    return helpers.json_response(levels)


def create_arranged_directory(system, record_id):
    """
    Creates a directory to house an arranged SIP associated with `record_id` in `system`.

    If a mapping already exists, returns the existing mapping.
    Otherwise, creates one along with a directory in the arranged directory tree.
    """
    identifier = _normalize_record_id(record_id)
    mapping, created = SIPArrangeAccessMapping.objects.get_or_create(system=system,
                                                                      identifier=identifier)
    if created:
        try:
            filepath = '/arrange/' + record_id + str(uuid.uuid4())  # TODO: get this from the title?
            filesystem_views.create_arrange_directory(filepath)
        except ValueError:
            mapping.delete()
            return
        else:
            mapping.arrange_path = filepath
            mapping.save()

    return mapping


def access_create_directory(request, system='', record_id=''):
    """
    Creates an arranged SIP directory for record `record_id` in `system`.
    """
    mapping = create_arranged_directory(system, record_id)
    if mapping is not None:
        response = {
            'success': True,
            'message': 'Creation successful.',
            'path': mapping.arrange_path,
        }
        status_code = 201
    else:
        response = {
            'success': False,
            'message': 'Could not create arrange directory.'
        }
        status_code = 400
    return helpers.json_response(response, status_code=status_code)


@_get_or_create_arrange_path
@_get_sip
def access_sip_rights(request, sip):
    return redirect('components.rights.views.ingest_rights_list', uuid=sip.uuid)


@_get_or_create_arrange_path
@_get_sip
def access_sip_metadata(request, sip):
    return redirect('components.ingest.views.ingest_metadata_list', uuid=sip.uuid)


def access_copy_to_arrange(request, system='', record_id=''):
    """
    Copies a record from POST parameter `filepath` into the SIP arrange directory for the specified record, creating a directory if necessary.

    This should be used to copy files into the root of the SIP, while filesystem_ajax's version of this API should be used to copy deeper into the record.
    """
    mapping = create_arranged_directory(system, record_id)
    if mapping is None:
        response = {
            'success': False,
            'message': 'Unable to create directory.'
        }
        return helpers.json_response(response, status_code=400)
    sourcepath = base64.b64decode(request.POST.get('filepath', '')).lstrip('/')
    return filesystem_views.copy_to_arrange(request, sourcepath=sourcepath, destination=mapping.arrange_path + '/')


@_get_arrange_path
def access_arrange_contents(request, mapping):
    """
    Lists the files in the root of the SIP arrange directory associated with this record.
    """
    return filesystem_views.arrange_contents(request, path=mapping.arrange_path + '/')


@_get_arrange_path
def access_arrange_start_sip(request, mapping):
    """
    Starts the SIP associated with this record.
    """
    ArchivesSpaceDOComponent.objects.filter(resourceid=mapping.identifier, started=False).update(started=True)
    return filesystem_views.copy_from_arrange_to_completed(request, filepath=mapping.arrange_path + '/')
