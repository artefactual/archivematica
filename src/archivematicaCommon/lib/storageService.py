from __future__ import absolute_import
import base64
import logging
import os
import platform
import requests
from requests.auth import AuthBase
import urllib

from django.conf import settings as django_settings

# archivematicaCommon
from archivematicaFunctions import get_setting

LOGGER = logging.getLogger("archivematica.common")


class ResourceNotFound(Exception):
    pass


class BadRequest(Exception):
    pass


class StorageServiceError(Exception):
    """Error related to the storage service."""


# ####################### INTERFACE WITH STORAGE API #########################

# ########### HELPER FUNCTIONS #############

class ApiKeyAuth(AuthBase):
    """Custom auth for requests that puts user & key in Authorization header."""

    def __init__(self, username=None, apikey=None):
        self.username = username or get_setting('storage_service_user', 'test')
        self.apikey = apikey or get_setting('storage_service_apikey', None)

    def __call__(self, r):
        r.headers['Authorization'] = "ApiKey {0}:{1}".format(self.username, self.apikey)
        return r


def _storage_service_url():
    # Get storage service URL from DashboardSetting model
    storage_service_url = get_setting('storage_service_url', None)
    if storage_service_url is None:
        LOGGER.error("Storage server not configured.")
        storage_service_url = 'http://localhost:8000/'
    # If the URL doesn't end in a /, add one
    if storage_service_url[-1] != '/':
        storage_service_url += '/'
    storage_service_url = storage_service_url + 'api/v2/'
    return storage_service_url


def _storage_api_session(timeout=django_settings.STORAGE_SERVICE_CLIENT_TIMEOUT):
    """Return a requests.Session with a customized adapter with timeout support."""
    class HTTPAdapterWithTimeout(requests.adapters.HTTPAdapter):
        def __init__(self, timeout=None, *args, **kwargs):
            self.timeout = timeout
            super(HTTPAdapterWithTimeout, self).__init__(*args, **kwargs)

        def send(self, *args, **kwargs):
            kwargs['timeout'] = self.timeout
            return super(HTTPAdapterWithTimeout, self).send(*args, **kwargs)

    session = requests.session()
    session.auth = ApiKeyAuth()
    session.mount('http://', HTTPAdapterWithTimeout(timeout=timeout))
    session.mount('https://', HTTPAdapterWithTimeout(timeout=timeout))
    return session


def _storage_api_quick_session():
    return _storage_api_session(django_settings.STORAGE_SERVICE_CLIENT_QUICK_TIMEOUT)


def _storage_api_params():
    """Return API GET params username=USERNAME&api_key=KEY for use in URL."""
    username = get_setting('storage_service_user', 'test')
    api_key = get_setting('storage_service_apikey', None)
    return urllib.urlencode({'username': username, 'api_key': api_key})


def _storage_relative_from_absolute(location_path, space_path):
    """Strip space_path and next / from location_path."""
    location_path = os.path.normpath(location_path)
    if location_path[0] == '/':
        strip = len(space_path)
        if location_path[strip] == '/':
            strip += 1
        location_path = location_path[strip:]
    return location_path

# ########### PIPELINE #############


def create_pipeline(create_default_locations=False, shared_path=None, api_username=None, api_key=None):
    pipeline = {
        'uuid': get_setting('dashboard_uuid'),
        'description': "Archivematica on {}".format(platform.node()),
        'create_default_locations': create_default_locations,
        'shared_path': shared_path,
        'api_username': api_username,
        'api_key': api_key,
    }
    LOGGER.info("Creating pipeline in storage service with %s", pipeline)
    url = _storage_service_url() + 'pipeline/'
    try:
        response = _storage_api_quick_session().post(url, json=pipeline)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        LOGGER.warning('Unable to create Archivematica pipeline in storage service from %s because %s', pipeline, e, exc_info=True)
        raise
    return True


def get_pipeline(uuid):
    url = _storage_service_url() + 'pipeline/' + uuid + '/'
    try:
        response = _storage_api_quick_session().get(url)
        if response.status_code == 404:
            LOGGER.warning("This Archivematica instance is not registered with the storage service or has been disabled.")
        response.raise_for_status()
    except requests.exceptions.RequestException:
        LOGGER.warning('Error fetching pipeline', exc_info=True)
        raise

    pipeline = response.json()
    return pipeline

# ########### LOCATIONS #############


def get_location(path=None, purpose=None, space=None):
    """ Returns a list of storage locations, filtered by parameters.

    Queries the storage service and returns a list of storage locations,
    optionally filtered by purpose, containing space or path.

    purpose: How the storage is used.  Should reference storage service
        purposes, found in storage_service.locations.models.py
    path: Path to location.  If a space is passed in, paths starting with /
        have the space's path stripped.
    """
    return_locations = []
    if space and path:
        path = _storage_relative_from_absolute(path, space['path'])
        space = space['uuid']
    pipeline = get_pipeline(get_setting('dashboard_uuid'))
    if pipeline is None:
        return None
    url = _storage_service_url() + 'location/'
    params = {
        'pipeline__uuid': pipeline['uuid'],
        'relative_path': path,
        'purpose': purpose,
        'space': space,
        'offset': 0,
    }
    while True:
        response = _storage_api_quick_session().get(url, params=params)
        locations = response.json()
        return_locations += locations['objects']
        if not locations['meta']['next']:
            break
        params['offset'] += locations['meta']['limit']

    LOGGER.debug("Storage locations returned: %s", return_locations)
    return return_locations


def browse_location(uuid, path):
    """
    Browse files in a location. Encodes path in base64 for transimission, returns decoded entries.
    """
    path = base64.b64encode(path)
    url = _storage_service_url() + 'location/' + uuid + '/browse/'
    params = {'path': path}
    response = _storage_api_quick_session().get(url, params=params)
    browse = response.json()
    browse['entries'] = map(base64.b64decode, browse['entries'])
    browse['directories'] = map(base64.b64decode, browse['directories'])
    browse['properties'] = {base64.b64decode(k): v for k, v in browse.get('properties', {}).items()}
    return browse


def copy_files(source_location, destination_location, files):
    """
    Copies `files` from `source_location` to `destination_location` using SS.

    source_location/destination_location: Dict with Location information, result
        of a call to get_location.
    files: List of dicts with source and destination paths relative to
        source_location and destination_location, respectively.  All other
        fields ignored.
    """
    pipeline = get_pipeline(get_setting('dashboard_uuid'))
    move_files = {
        'origin_location': source_location['resource_uri'],
        'files': files,
        'pipeline': pipeline['resource_uri'],
    }

    # Here we attempt to decode the 'source' attributes of each move-file to
    # Unicode prior to passing to Slumber's ``post`` method. Slumber will do
    # this anyway and will choke in certain specific cases, specifically where
    # the JavaScript of the dashboard has base-64-encoded a Latin-1-encoded
    # string.
    for file_ in move_files['files']:
        try:
            file_['source'] = file_['source'].decode('utf8')
        except UnicodeDecodeError:
            try:
                file_['source'] = file_['source'].decode('latin-1')
            except UnicodeError:
                pass

    url = _storage_service_url() + 'location/' + destination_location['uuid'] + '/'
    try:
        response = _storage_api_session().post(url, json=move_files)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        LOGGER.warning("Unable to move files with %s because %s", move_files, e.content)
        return (None, e)
    ret = response.json()
    return (ret, None)


def get_files_from_backlog(files):
    """
    Copies files from the backlog location to the currently processing location.
    See copy_files for more details.
    """
    # Get Backlog location UUID
    # Assuming only one backlog location
    backlog = get_location(purpose='BL')[0]
    # Get currently processing location
    processing = get_location(purpose='CP')[0]

    return copy_files(backlog, processing, files)


# ########### FILES #############

def create_file(uuid, origin_location, origin_path, current_location,
                current_path, package_type, size, update=False, related_package_uuid=None):
    """ Creates a new file. Returns a tuple of (resulting dict, None) on success, (None, error) on failure.

    origin_location and current_location should be URIs for the storage service.
    """
    pipeline = get_pipeline(get_setting('dashboard_uuid'))
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
        'related_package_uuid': related_package_uuid
    }

    LOGGER.info("Creating file with %s", new_file)
    try:
        session = _storage_api_session()
        if update:
            new_file['reingest'] = pipeline['uuid']
            url = _storage_service_url() + 'file/' + uuid + '/'
            response = session.put(url, json=new_file)
        else:
            url = _storage_service_url() + 'file/'
            response = session.post(url, json=new_file)
    except requests.exceptions.RequestException as e:
        LOGGER.warning("Unable to create file from %s because %s", new_file, e)
        return (None, e)
    file_ = response.json()
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
    return_files = []
    url = _storage_service_url() + 'file/'
    params = {
        'uuid': uuid,
        'origin_location': origin_location,
        'origin_path': origin_path,
        'current_location': current_location,
        'current_path': current_path,
        'package_type': package_type,
        'status': status,
        'offset': 0,
    }
    while True:
        response = _storage_api_session().get(url, params=params)
        files = response.json()
        return_files += files['objects']
        if not files['meta']['next']:
            break
        params['offset'] += files['meta']['limit']

    LOGGER.debug("Files returned: %s", return_files)
    return return_files


def download_file_url(file_uuid):
    """
    Returns URL to storage service for downloading `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    params = _storage_api_params()
    download_url = "{base_url}file/{uuid}/download/?{params}".format(
        base_url=storage_service_url, uuid=file_uuid, params=params)
    return download_url


def extract_file_url(file_uuid, relative_path):
    """
    Returns URL to storage service for `relative_path` in `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    api_params = _storage_api_params()
    download_url = "{base_url}file/{uuid}/extract_file/?relative_path_to_file={path}&{params}".format(
        base_url=storage_service_url, uuid=file_uuid, path=relative_path, params=api_params)
    return download_url


def extract_file(uuid, relative_path, save_path):
    """ Fetches `relative_path` from package with `uuid` and saves to `save_path`. """
    url = _storage_service_url() + 'file/' + uuid + '/extract_file/'
    params = {'relative_path_to_file': relative_path}
    response = _storage_api_session().get(url, params=params, stream=True)
    chunk_size = 1024 * 1024
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size):
            f.write(chunk)
    os.chmod(save_path, 0o660)


def pointer_file_url(file_uuid):
    """
    Returns URL to storage service for pointer file for `file_uuid`.
    """
    storage_service_url = _storage_service_url()
    params = _storage_api_params()
    download_url = "{base_url}file/{uuid}/pointer_file/?{params}".format(
        base_url=storage_service_url, uuid=file_uuid, params=params)
    return download_url


def request_reingest(package_uuid, reingest_type, processing_config):
    """
    Requests `package_uuid` for reingest in this pipeline.

    `reingest_type` determines what files will be copied for reingest, defined
    by ReingestAIPForm.REINGEST_CHOICES.

    Returns a dict: {'error': [True|False], 'message': '<error message>'}
    """
    api_request = {
        'pipeline': get_setting('dashboard_uuid'),
        'reingest_type': reingest_type,
        'processing_config': processing_config,
    }
    url = _storage_service_url() + 'file/' + package_uuid + '/reingest/'
    try:
        response = _storage_api_session().post(url, json=api_request)
    except requests.ConnectionError:
        LOGGER.exception("Could not connect to storage service")
        return {'error': True, 'message': 'Could not connect to storage service'}
    except requests.exceptions.RequestException:
        LOGGER.exception("Unable to reingest %s", package_uuid)
        try:
            return response.json()
        except Exception:
            return {'error': True}
    return response.json()


def request_file_deletion(uuid, user_id, user_email, reason_for_deletion):
    """ Returns the server response. """

    api_request = {
        'event_reason': reason_for_deletion,
        'pipeline': get_setting('dashboard_uuid'),
        'user_email': user_email,
        'user_id': user_id,
    }
    url = _storage_service_url() + 'file/' + uuid + '/delete_aip/'
    response = _storage_api_quick_session().post(url, json=api_request)
    return response.json()


def post_store_aip_callback(uuid):
    url = _storage_service_url() + 'file/' + uuid + '/send_callback/post_store/'
    response = _storage_api_session().get(url)
    try:
        return response.json()
    except Exception:
        return response.text


def get_file_metadata(**kwargs):
    url = _storage_service_url() + 'file/metadata/'
    response = _storage_api_session().get(url, params=kwargs)
    if 400 <= response.status_code < 500:
        raise ResourceNotFound("No file found for arguments: {}".format(kwargs))
    return response.json()


def remove_files_from_transfer(transfer_uuid):
    url = _storage_service_url() + 'file/' + transfer_uuid + '/contents/'
    _storage_api_session().delete(url)


def index_backlogged_transfer_contents(transfer_uuid, file_set):
    url = _storage_service_url() + 'file/' + transfer_uuid + '/contents/'
    response = _storage_api_session().put(url, json=file_set)
    if 400 <= response.status_code < 500:
        raise BadRequest("Unable to add files to transfer: {}".format(response.text))
