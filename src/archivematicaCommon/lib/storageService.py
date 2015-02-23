import base64
import logging
import os
import platform
import slumber
import sys

sys.path.append("/usr/share/archivematica/dashboard")
from main.models import DashboardSetting

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)


class ResourceNotFound(Exception):
    pass

class BadRequest(Exception):
    pass

######################### INTERFACE WITH STORAGE API #########################

############# HELPER FUNCTIONS #############

def get_setting(setting, default=''):
    try:
        return DashboardSetting.objects.get(name=setting).value
    except DashboardSetting.DoesNotExist:
        return default

def _storage_service_url():
    # Get storage service URL from DashboardSetting model
    storage_service_url = get_setting('storage_service_url', None)
    if storage_service_url is None:
        logging.error("Storage server not configured.")
        storage_service_url = 'http://localhost:8000/'
    # If the URL doesn't end in a /, add one
    if storage_service_url[-1] != '/':
        storage_service_url+='/'
    storage_service_url = storage_service_url+'api/v2/'
    logging.debug("Storage service URL: {}".format(storage_service_url))
    return storage_service_url


def _storage_api():
    """ Returns slumber access to storage API. """
    storage_service_url = _storage_service_url()
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

def create_pipeline(create_default_locations=False, shared_path=None, api_username=None, api_key=None):
    api = _storage_api()
    pipeline = {
        'uuid': get_setting('dashboard_uuid'),
        'description': "Archivematica on {}".format(platform.node()),
        'create_default_locations': create_default_locations,
        'shared_path': shared_path,
        'api_username': api_username,
        'api_key': api_key,
    }
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
    """
    Browse files in a location. Encodes path in base64 for transimission, returns decoded entries.
    """
    api = _storage_api()
    path = base64.b64encode(path)
    browse = api.location(uuid).browse.get(path=path)
    browse['entries'] = map(base64.b64decode, browse['entries'])
    browse['directories'] = map(base64.b64decode, browse['directories'])
    return browse

def copy_files(source_location, destination_location, files, api=None):
    """
    Copies `files` from `source_location` to `destination_location` using SS.

    source_location/destination_location: Dict with Location information, result
        of a call to get_location or get_location_by_uri.
    files: List of dicts with source and destination paths relative to
        source_location and destination_location, respectively.  All other
        fields ignored.
    """
    if api is None:
        api = _storage_api()
    pipeline = _get_pipeline(get_setting('dashboard_uuid'))
    move_files = {
        'origin_location': source_location['resource_uri'],
        'files': files,
        'pipeline': pipeline['resource_uri'],
    }
    try:
        ret = api.location(destination_location['uuid']).post(move_files)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to move files with {} because {}".format(move_files, e.content))
        return (None, e)
    except slumber.exceptions.HttpServerError as e:
        logging.warning("Could not connect to storage service: {} ({})".format(
            e, e.content))
        return (None, e)
    return (ret, None)

def get_files_from_backlog(files):
    """
    Copies files from the backlog location to the currently processing location.
    See copy_files for more details.
    """
    api = _storage_api()

    # Get Backlog location UUID
    # Assuming only one backlog location
    backlog = get_location(purpose='BL')[0]
    # Get currently processing location
    processing = get_location(purpose='CP')[0]

    return copy_files(backlog, processing, files, api)


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

def download_file_url(file_uuid):
    """
    Returns URL to storage service for downloading `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    download_url = "{base_url}file/{uuid}/download/".format(
        base_url=storage_service_url, uuid=file_uuid)
    return download_url

def extract_file_url(file_uuid, relative_path):
    """
    Returns URL to storage service for `relative_path` in `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    download_url = "{base_url}file/{uuid}/extract_file/?relative_path_to_file={path}".format(
        base_url=storage_service_url, uuid=file_uuid, path=relative_path)
    return download_url

def extract_file(uuid, relative_path, save_path):
    """ Fetches `relative_path` from package with `uuid` and saves to `save_path`. """
    api = _storage_api()
    params = {'relative_path_to_file': relative_path}
    with open(save_path, 'w') as f:
        f.write(api.file(uuid).extract_file.get(**params))
        os.chmod(save_path, 0o660)


def pointer_file_url(file_uuid):
    """
    Returns URL to storage service for pointer file for `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    download_url = "{base_url}file/{uuid}/pointer_file/".format(
        base_url=storage_service_url, uuid=file_uuid)
    return download_url


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


def post_store_aip_callback(uuid):
    api = _storage_api()
    return api.file(uuid).send_callback.post_store.get()

def get_file_metadata(**kwargs):
    api = _storage_api()
    try:
        return api.file.metadata.get(**kwargs)
    except slumber.exceptions.HttpClientError:
        raise ResourceNotFound("No file found for arguments: {}".format(kwargs))

def remove_files_from_transfer(transfer_uuid):
    api = _storage_api()
    api.file(transfer_uuid).contents.delete()

def index_backlogged_transfer_contents(transfer_uuid, file_set):
    api = _storage_api()
    try:
        api.file(transfer_uuid).contents.put(file_set)
    except slumber.exceptions.HttpClientError as e:
        raise BadRequest("Unable to add files to transfer: {}".format(e))
