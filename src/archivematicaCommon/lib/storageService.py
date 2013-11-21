import logging
import os
import platform
import slumber
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)

dashboard_path = '/usr/share/archivematica/dashboard'
if dashboard_path not in sys.path:
    sys.path.append(dashboard_path)
from components.helpers import get_setting

######################### INTERFACE WITH STORAGE API #########################

############# HELPER FUNCTIONS #############

def _storage_api():
    """ Returns slumber access to storage API. """
    # Get storage service URL from DashboardSetting model
    storage_service_url = get_setting('storage_service_url', None)
    if storage_service_url is None:
        logging.error("Storage server not configured.")
        storage_service_url = 'http://localhost:8000/'
    # If the URL doesn't end in a /, add one
    if storage_service_url[-1] != '/':
        storage_service_url+='/'
    storage_service_url = storage_service_url+'api/v1/'
    logging.debug("Storage service URL: {}".format(storage_service_url))
    api = slumber.API(storage_service_url)
    return api

def _storage_relative_from_absolute(location_path, space_path):
    """ Strip space_path and next / from location_path. """
    location_path = os.path.normpath(location_path)
    if location_path[0] == '/':
        strip = len(space_path)
        if location_path[strip] == '/':
            strip += 1
        location_path = location_path[strip:]
    return location_path

############# PIPELINE #############

def create_pipeline(create_default_locations=False, shared_path=None):
    api = _storage_api()
    pipeline = {}
    pipeline['uuid'] = get_setting('dashboard_uuid')
    pipeline['description'] = "Archivematica on {}".format(platform.node())
    pipeline['create_default_locations'] = create_default_locations
    pipeline['shared_path'] = shared_path
    logging.info("Creating pipeline in storage service with {}".format(pipeline))
    try:
        api.pipeline.post(pipeline)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to create Archivematica pipeline in storage service from {} because {}".format(pipeline, e.content))
        return False
    except slumber.exceptions.HttpServerError as e:
        if 'column uuid is not unique' in e.content:
            pass
        else:
            raise
    return True

def _get_pipeline(uuid):
    api = _storage_api()
    try:
        pipeline = api.pipeline(uuid).get()
    except slumber.exceptions.HttpClientError as e:
        if e.response.status_code == 404:
            logging.warning("This Archivematica instance is not registered with the storage service or has been disabled.")
        pipeline = None
    return pipeline

############# LOCATIONS #############

def get_location(path=None, purpose=None, space=None):
    """ Returns a list of storage locations, filtered by parameters.

    Queries the storage service and returns a list of storage locations,
    optionally filtered by purpose, containing space or path.

    purpose: How the storage is used.  Should reference storage service
        purposes, found in storage_service.locations.models.py
    path: Path to location.  If a space is passed in, paths starting with /
        have the space's path stripped.
    """
    api = _storage_api()
    offset = 0
    return_locations = []
    if space and path:
        path = _storage_relative_from_absolute(path, space['path'])
        space = space['uuid']
    pipeline = _get_pipeline(get_setting('dashboard_uuid'))
    if pipeline is None:
        return None
    while True:
        locations = api.location.get(pipeline__uuid=pipeline['uuid'],
                                     relative_path=path,
                                     purpose=purpose,
                                     space=space,
                                     offset=offset)
        logging.debug("Storage locations retrieved: {}".format(locations))
        return_locations += locations['objects']
        if not locations['meta']['next']:
            break
        offset += locations['meta']['limit']

    logging.info("Storage locations returned: {}".format(return_locations))
    return return_locations

def get_location_by_uri(uri):
    """ Get a specific location by the URI.  Only returns one location. """
    api = _storage_api()
    # TODO check that location is associated with this pipeline
    return api.location(uri).get()

def browse_location(uuid, path):
    """ Browse files in a location. """
    api = _storage_api()
    return api.location(uuid).browse.get(path=path)

############# SPACES #############

def get_space(access_protocol=None, path=None):
    """ Returns a list of storage spaces, optionally filtered by parameters.

    Queries the storage service and returns a list of storage spaces,
    optionally filtered by access_protocol or path.

    access_protocol: How the storage is accessed.  Should reference storage
        service purposes, in storage_service.locations.models.py
    """
    api = _storage_api()
    offset = 0
    return_spaces = []
    while True:
        spaces = api.space.get(access_protocol=access_protocol,
                               path=path,
                               offset=offset)
        logging.debug("Storage spaces retrieved: {}".format(spaces))
        return_spaces += spaces['objects']
        if not spaces['meta']['next']:
            break
        offset += spaces['meta']['limit']

    logging.info("Storage spaces returned: {}".format(return_spaces))
    return return_spaces

############# FILES #############

def create_file(uuid, origin_location, origin_path, current_location,
        current_path, package_type, size):
    """ Creates a new file. Returns a tuple of (resulting dict, None) on success, (None, error) on failure.

    origin_location and current_location should be URIs for the storage service.
    """

    api = _storage_api()
    pipeline = _get_pipeline(get_setting('dashboard_uuid'))
    if pipeline is None:
        return (None, 'Pipeline not available, see logs.')
    new_file = {
        'uuid': uuid,
        'origin_location': origin_location,
        'origin_path': origin_path,
        'current_location': current_location,
        'current_path': current_path,
        'package_type': package_type,
        'size': size,
        'origin_pipeline': pipeline['resource_uri'],
    }

    logging.info("Creating file with {}".format(new_file))
    try:
        file_ = api.file.post(new_file)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to create file from {} because {}".format(new_file, e.content))
        return (None, e)
    except slumber.exceptions.HttpServerError as e:
        logging.warning("Could not connect to storage service: {} ({})".format(
            e, e.content))
        return (None, e)
    return (file_, None)

def get_file_info(uuid=None, origin_location=None, origin_path=None,
        current_location=None, current_path=None, package_type=None,
        status=None):
    """ Returns a list of files, optionally filtered by parameters.

    Queries the storage service and returns a list of files,
    optionally filtered by origin location/path, current location/path, or
    package_type.
    """
    # TODO Need a better way to deal with mishmash of relative and absolute
    # paths coming in
    api = _storage_api()
    offset = 0
    return_files = []
    while True:
        files = api.file.get(uuid=uuid,
                             origin_location=origin_location,
                             origin_path=origin_path,
                             current_location=current_location,
                             current_path=current_path,
                             package_type=package_type,
                             status=status,
                             offset=offset)
        logging.debug("Files retrieved: {}".format(files))
        return_files += files['objects']
        if not files['meta']['next']:
            break
        offset += files['meta']['limit']

    logging.info("Files returned: {}".format(return_files))
    return return_files

def request_file_deletion(uuid, user_id, user_email, reason_for_deletion):
    """ Returns the server response. """

    api = _storage_api()
    api_request = {
        'event_reason': reason_for_deletion,
        'pipeline':     get_setting('dashboard_uuid'),
        'user_email':   user_email,
        'user_id':      user_id
    }

    return api.file(uuid).delete_aip.post(api_request)
