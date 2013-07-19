import logging
import os
import slumber

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log",
    level=logging.INFO)


######################### INTERFACE WITH STORAGE API #########################

############# HELPER FUNCTIONS #############

def _storage_api():
    """ Returns slumber access to storage API. """
    # TODO get this from config
    storage_server = "http://localhost:8000/api/v1/"
    api = slumber.API(storage_server)
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

############# LOCATIONS #############

def create_location(purpose, path, description=None, space=None, quota=None, used=0):
    """ Creates a storage location.  Returns resulting dict on success, false on failure.

    purpose: How the storage is used.  Should reference storage service
        purposes, found in storage_service.locations.models.py
    path: Path to location.
    space: storage space to put the location in.  The space['path'] will be
        stripped off the start of path if path is absolute.

    Dashboard may only create locations on the local filesystem.  If no space
    is provided, it will try to find an existing storage space to put the
    location in, matching based on path.
    """
    api = _storage_api()

    # If no space provided, try to find space with common prefix with path
    if not space:
        spaces = get_space(access_protocol="FS")
        try:
            space = filter(lambda s: path.startswith(s['path']),
                spaces)[0]
        except IndexError as e:
            logging.warning("No storage space containing {}".format(path))
            return False

    path = _storage_relative_from_absolute(path, space['path'])

    new_location = {}
    new_location['purpose'] = purpose
    new_location['relative_path'] = path
    new_location['description'] = description
    new_location['quota'] = quota
    new_location['used'] = used
    new_location['space'] = space['resource_uri']

    logging.info("Creating storage location with {}".format(new_location))
    try:
        location = api.location.post(new_location)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to create storage location from {} because {}".format(new_location, e.content))
        return False
    return location

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
    if space:
        path = _storage_relative_from_absolute(path, space['path'])
        space = space['uuid']
    while True:
        locations = api.location.get(relative_path=path,
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
    return api.location(uri).get()

def delete_location(uuid):
    """ Deletes storage with UUID uuid, returns True on success."""
    api = _storage_api()
    logging.info("Deleting storage location with UUID {}".format(uuid))
    ret = api.location(str(uuid)).patch({'disabled': True})
    return ret['disabled']

############# SPACES #############

def create_space(path, access_protocol, size=None, used=0):
    """ Creates a new storage space. Returns resulting dict on success, false on failure.

    access_protocol: How the storage is accessed.  Should reference storage
        service purposes, in storage_service.locations.models.py
        Currently, dashboard can only create local FS locations.
    size: Size of storage space, in bytes.  Default: unlimited
    used: Space used in storage space, in bytes.
    """
    api = _storage_api()

    new_space = {}
    new_space['path'] = path
    new_space['access_protocol'] = access_protocol
    new_space['size'] = size
    new_space['used'] = used

    if access_protocol != "FS":
        logging.warning("Trying to create storage space with access protocol {}".format(access_protocol))

    logging.info("Creating storage space with {}".format(new_space))
    try:
        space = api.space.post(new_space)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to create storage space from {} because {}".format(new_space, e.content))
        return False
    return space

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
        current_path, package_type):
    """ Creates a new file. Returns resulting dict on success, None on failure.

    origin_location and current_location should be URIs for the storage service.
    """

    api = _storage_api()

    new_file = {}
    new_file['uuid'] = uuid
    new_file['origin_location'] = origin_location
    new_file['origin_path'] = origin_path
    new_file['current_location'] = current_location
    new_file['current_path'] = current_path
    new_file['package_type'] = package_type

    logging.info("Creating file with {}".format(new_file))
    try:
        file_ = api.file.post(new_file)
    except slumber.exceptions.HttpClientError as e:
        logging.warning("Unable to create file from {} because {}".format(new_file, e.content))
        return None
    except slumber.exceptions.HttpServerError as e:
        logging.warning("Could not connect to storage service: {} ({})".format(
            e, e.content))
        return None
    return file_

def get_file_info(uuid=None, origin_location=None, origin_path=None,
        current_location=None, current_path=None, package_type=None):
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
                             offset=offset)
        logging.debug("Files retrieved: {}".format(files))
        return_files += files['objects']
        if not files['meta']['next']:
            break
        offset += files['meta']['limit']

    logging.info("Files returned: {}".format(return_files))
    return return_files
