# Standard library, alphabetical by import source
from functools import wraps
import json
import logging
import sys

# Django Core, alphabetical by import source
import django.http

# External dependencies, alphabetical
import MySQLdb  # for ATK exceptions

# This project, alphabetical by import source
from components import helpers
from components.ingest.views_atk import get_atk_system_client
from components.ingest.views_as import get_as_system_client

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivistsToolkit.client import ArchivistsToolkitError
from archivesspace.client import ArchivesSpaceError, AuthenticationError

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


@_authenticate_to_archivesspace
def all_records(client, request, system=''):
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 30)
    search_pattern = request.GET.get('title', '')
    identifier = request.GET.get('identifier', '')

    return helpers.json_response(client.find_collections(search_pattern=search_pattern,
                                                         identifier=identifier,
                                                         page=page,
                                                         page_size=page_size))


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
        record_id = record_id.replace('-', '/')

        try:
            records = client.get_resource_component_and_children(record_id,
                                                                 recurse_max_level=3)
            return helpers.json_response(records)
        except ArchivesSpaceError as e:
            return helpers.json_response({'success': False, "message": str(e)}, status_code=400)


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
    record_id = record_id.replace('-', '/')

    if request.method == 'POST':
        new_record_data = json.load(request)
        try:
            new_id = client.add_child(record_id,
                                      title=new_record_data.get('title', ''),
                                      level=new_record_data.get('level', ''))
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
        return helpers.json_response(records['children'])


@_authenticate_to_archivesspace
def get_levels_of_description(client, request, system=''):
    levels = client.get_levels_of_description()
    return helpers.json_response(levels)
