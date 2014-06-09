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

import base64
import errno
import os
import logging
import re
import shutil
import sys
import tempfile
import uuid

import django.http
from django.db import connection, IntegrityError

from components import helpers
import components.filesystem_ajax.helpers as filesystem_ajax_helpers
from main import models

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import databaseFunctions
import elasticSearchFunctions
import storageService as storage_service

# for unciode sorting support
import locale
locale.setlocale(locale.LC_ALL, '')

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

SHARED_DIRECTORY_ROOT   = '/var/archivematica/sharedDirectory'
ACTIVE_TRANSFER_DIR     = SHARED_DIRECTORY_ROOT + '/watchedDirectories/activeTransfers'
STANDARD_TRANSFER_DIR   = ACTIVE_TRANSFER_DIR + '/standardTransfer'
ORIGINAL_DIR            = SHARED_DIRECTORY_ROOT + '/www/AIPsStore/transferBacklog/originals'

DEFAULT_BACKLOG_PATH = 'originals/'
DEFAULT_ARRANGE_PATH = '/arrange/'


def directory_children_proxy_to_storage_server(request, location_uuid, basePath=False):
    path = ''
    if (basePath):
        path = base64.b64decode(basePath)
    path = path + base64.b64decode(request.GET.get('base_path', ''))
    path = path + base64.b64decode(request.GET.get('path', ''))

    response = storage_service.browse_location(location_uuid, path)
    response['entries'] = map(base64.b64encode, response['entries'])
    response['directories'] = map(base64.b64encode, response['directories'])

    return helpers.json_response(response)

def contents(request):
    path = request.GET.get('path', '/home')
    response = filesystem_ajax_helpers.directory_to_dict(path)
    return helpers.json_response(response)

def arrange_contents(request):
    base_path = base64.b64decode(request.GET.get('path', DEFAULT_ARRANGE_PATH))

    # Must indicate that base_path is a folder by ending with /
    if not base_path.endswith('/'):
        base_path += '/'

    if not base_path.startswith(DEFAULT_ARRANGE_PATH):
        base_path = DEFAULT_ARRANGE_PATH

    # Query SIP Arrangement for results
    # Get all the paths that are not in SIPs and start with base_path.  We don't
    # need the objects, just the arrange_path
    paths = models.SIPArrange.objects.filter(sip_created=False).filter(aip_created=False).filter(arrange_path__startswith=base_path).order_by('arrange_path').values_list('arrange_path', flat=True)

    # Convert the response into an entries [] and directories []
    # 'entries' contains everything (files and directories)
    response = {'entries': [], 'directories': []}
    for path in paths:
        # Stip common prefix
        if path.startswith(base_path):
            path = path[len(base_path):]
        entry = path.split('/', 1)[0]
        entry = base64.b64encode(entry)
        # Only insert once
        if entry and entry not in response['entries']:
            response['entries'].append(entry)
            if path.endswith('/'):  # path is a dir
                response['directories'].append(entry)

    return helpers.json_response(response)


def delete(request):
    filepath = request.POST.get('filepath', '')
    filepath = os.path.join('/', filepath)
    error = filesystem_ajax_helpers.check_filepath_exists(filepath)

    if error == None:
        if os.path.isdir(filepath):
            try:
                shutil.rmtree(filepath)
            except Exception:
                logging.exception('Error deleting directory {}'.format(filepath))
                error = 'Error attempting to delete directory.'
        else:
            os.remove(filepath)

    # if deleting from originals, delete ES data as well
    if ORIGINAL_DIR in filepath and filepath.index(ORIGINAL_DIR) == 0:
        transfer_uuid = _find_uuid_of_transfer_in_originals_directory_using_path(filepath)
        if transfer_uuid != None:
            elasticSearchFunctions.connect_and_remove_backlog_transfer_files(transfer_uuid)

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'Delete successful.'}

    return helpers.json_response(response)


def delete_arrange(request):
    filepath = base64.b64decode(request.POST.get('filepath', ''))
    models.SIPArrange.objects.filter(arrange_path__startswith=filepath).delete()
    return helpers.json_response({'message': 'Delete successful.'})


def get_temp_directory(request):
    temp_base_dir = helpers.get_client_config_value('temp_dir')

    response = {}

    # use system temp dir if none specifically defined
    if temp_base_dir == '':
        temp_dir = tempfile.mkdtemp()
    else:
        try:
            temp_dir = tempfile.mkdtemp(dir=temp_base_dir)
        except:
            temp_dir = ''
            response['error'] = 'Unable to create temp directory.'

    #os.chmod(temp_dir, 0o777)

    response['tempDir'] = temp_dir

    return helpers.json_response(response)


def start_transfer(request):
    transfer_name = archivematicaFunctions.unicodeToStr(request.POST.get('name', ''))
    # Note that the path may contain arbitrary, non-unicode characters,
    # and hence is POSTed to the server base64-encoded
    transfer_type = archivematicaFunctions.unicodeToStr(request.POST.get('type', ''))
    accession = archivematicaFunctions.unicodeToStr(request.POST.get('accession', ''))
    paths = request.POST.getlist('paths[]', [])
    paths = [base64.b64decode(path) for path in paths]
    row_ids = request.POST.getlist('row_ids[]', [])

    # Create temp directory that everything will be copied into
    temp_base_dir = helpers.get_client_config_value('temp_dir') or None
    temp_dir = tempfile.mkdtemp(dir=temp_base_dir)

    for i, path in enumerate(paths):
        index = i + 1  # so transfers start from 1, not 0
        # Don't suffix the first transfer component, only subsequent ones
        if index > 1:
            target = transfer_name + '_' + str(index)
        else:
            target = transfer_name
        row_id = row_ids[i]
        copy_transfer_component(transfer_name=target,
                                path=path, destination=temp_dir)

        if helpers.file_is_an_archive(path):
            filepath = os.path.join(temp_dir, os.path.basename(path))
        else:
            filepath = os.path.join(temp_dir, target)
        copy_to_start_transfer(filepath=filepath,
                               type=transfer_type, accession=accession,
                               transfer_metadata_set_row_uuid=row_id)

    response = {'message': 'Copy successful.'}
    return helpers.json_response(response)

def copy_transfer_component(transfer_name='', path='', destination=''):
    error = None

    if transfer_name == '':
        error = 'No transfer name provided.'
    else:
        if path == '':
            error = 'No path provided.'
        else:
            # if transfer compontent path leads to an archive, treat as zipped
            # bag
            if helpers.file_is_an_archive(path):
                filesystem_ajax_helpers.rsync_copy(path, destination)
                paths_copied = 1
            else:
                transfer_dir = os.path.join(destination, transfer_name)

                # Create directory before it is used, otherwise shutil.copy()
                # would that location to store a file
                if not os.path.isdir(transfer_dir):
                    os.mkdir(transfer_dir)

                paths_copied = 0

                # cycle through each path copying files/dirs
                # inside it to transfer dir
                try:
                    entries = filesystem_ajax_helpers.sorted_directory_list(path)
                except os.error as e:
                    error = "Error: {e.strerror}: {e.filename}".format(e=e)
                    # Clean up temp dir - don't use os.removedirs because
                    # <shared_path>/tmp might not have anything else in it and
                    # we don't want to delete it
                    os.rmdir(transfer_dir)
                    os.rmdir(destination)
                else:
                    for entry in entries:
                        entry_path = os.path.join(str(path), str(entry))
                        filesystem_ajax_helpers.rsync_copy(entry_path, transfer_dir)
                        paths_copied = paths_copied + 1

    if error:
        raise Exception(error)

    return paths_copied

def copy_to_start_transfer(filepath='', type='', accession='', transfer_metadata_set_row_uuid=''):
    error = filesystem_ajax_helpers.check_filepath_exists(filepath)

    if error == None:
        # confine destination to subdir of originals
        basename = os.path.basename(filepath)

        # default to standard transfer
        type_paths = {
          'standard':     'standardTransfer',
          'unzipped bag': 'baggitDirectory',
          'zipped bag':   'baggitZippedDirectory',
          'dspace':       'Dspace',
          'maildir':      'maildir',
          'TRIM':         'TRIM'
        }

        try:
          type_subdir = type_paths[type]
          destination = os.path.join(ACTIVE_TRANSFER_DIR, type_subdir)
        except KeyError:
          destination = os.path.join(STANDARD_TRANSFER_DIR)

        # if transfer compontent path leads to a ZIP file, treat as zipped
        # bag
        if not helpers.file_is_an_archive(filepath):
            destination = os.path.join(destination, basename)
            destination = helpers.pad_destination_filepath_if_it_already_exists(destination)

        # relay accession via DB row that MCPClient scripts will use to get
        # supplementary info from
        if accession != '' or transfer_metadata_set_row_uuid != '':
            temp_uuid = uuid.uuid4().__str__()
            mcp_destination = destination.replace(SHARED_DIRECTORY_ROOT + '/', '%sharedPath%') + '/'
            kwargs = {
                "uuid": temp_uuid,
                "accessionid": accession,
                "currentlocation": mcp_destination
            }

            # Even if a UUID is passed, there might not be a row with
            # that UUID yet - for instance, if the user opened an edit
            # form but did not save any metadata for that row.
            if transfer_metadata_set_row_uuid:
                try:
                    row = models.TransferMetadataSet.objects.get(
                        id="transfer_metadata_set_row_uuid"
                    )
                    kwargs["transfermetadatasetrow"] = row
                except models.TransferMetadataSet.DoesNotExist:
                    pass

            transfer = models.Transfer.objects.create(**kwargs)
            transfer.save()

        try:
            shutil.move(filepath, destination)
        except:
            error = 'Error copying from ' + filepath + ' to ' + destination + '. (' + str(sys.exc_info()[0]) + ')'

    if error:
        raise Exception(error)


def create_arranged_sip(staging_sip_path, files):
    shared_dir = helpers.get_server_config_value('sharedDirectory')
    staging_sip_path = staging_sip_path.lstrip('/')
    staging_abs_path = os.path.join(shared_dir, staging_sip_path)

    # Create SIP object
    sip_uuid = str(uuid.uuid4())
    sip_name = staging_sip_path.split('/')[1]
    sip_path = os.path.join(shared_dir, 'watchedDirectories', 'SIPCreation', 'SIPsUnderConstruction', sip_name)
    sip_path = helpers.pad_destination_filepath_if_it_already_exists(sip_path)
    sip_uuid = databaseFunctions.createSIP(sip_path.replace(shared_dir, '%sharedPath%', 1)+'/', sip_uuid)

    # Update currentLocation of files
    for file_ in files:
        if file_.get('uuid'):
            # Strip 'arrange/sip_name' from file path
            in_sip_path = '/'.join(file_['destination'].split('/')[2:])
            currentlocation = '%SIPDirectory%'+ in_sip_path
            models.File.objects.filter(uuid=file_['uuid']).update(sip=sip_uuid, currentlocation=currentlocation)

    # Create directories for logs and metadata, if they don't exist
    for directory in ('logs', 'metadata', os.path.join('metadata', 'submissionDocumentation')):
        try:
            os.mkdir(os.path.join(staging_abs_path, directory))
        except os.error as exception:
            if exception.errno != errno.EEXIST:
                raise

    # Add log of original location and new location of files
    arrange_log = os.path.join(staging_abs_path, 'logs', 'arrange.log')
    with open(arrange_log, 'w') as f:
        log = ('%s -> %s\n' % (file_['source'], file_['destination']) for file_ in files if file_.get('uuid'))
        f.writelines(log)

    # Move to watchedDirectories/SIPCreation/SIPsUnderConstruction
    logging.info('create_arranged_sip: move from %s to %s', staging_abs_path, sip_path)
    shutil.move(src=staging_abs_path, dst=sip_path)


def copy_from_arrange_to_completed(request):
    """ Create a SIP from the information stored in the SIPArrange table.

    Get all the files in the new SIP, and all their associated metadata, and
    move to the processing space.  Create needed database entries for the SIP
    and start the microservice chain.
    """
    error = None
    filepath = base64.b64decode(request.POST.get('filepath', ''))
    logging.info('copy_from_arrange_to_completed: filepath: %s', filepath)

    # Error checking
    if not filepath.startswith(DEFAULT_ARRANGE_PATH):
        # Must be in DEFAULT_ARRANGE_PATH
        error = '{} is not in {}'.format(filepath, DEFAULT_ARRANGE_PATH)
    elif not filepath.endswith('/'):
        # Must be a directory (end with /)
        error = '{} is not a directory'.format(filepath)
    else:
        # Filepath is prefix on arrange_path in SIPArrange
        sip_name = os.path.basename(filepath.rstrip('/'))
        staging_sip_path = os.path.join('staging', sip_name, '')
        logging.debug('copy_from_arrange_to_completed: staging_sip_path: %s', staging_sip_path)
        # Fetch all files with 'filepath' as prefix, and have a source path
        arrange = models.SIPArrange.objects.filter(sip_created=False).filter(arrange_path__startswith=filepath).filter(original_path__isnull=False)

        # Collect file information.  Change path to be in staging, not arrange
        files = []
        for arranged_file in arrange:
            files.append(
                {'source': arranged_file.original_path.lstrip('/'),
                 'destination': arranged_file.arrange_path.replace(
                    filepath, staging_sip_path, 1),
                 'uuid': arranged_file.file_uuid,
                }
            )
            # Get transfer folder name
            transfer_name = arranged_file.original_path.replace(
                DEFAULT_BACKLOG_PATH, '', 1).split('/', 1)[0]
            # Copy metadata & logs to completedTransfers, where later scripts expect
            for directory in ('logs', 'metadata'):
                file_ = {
                    'source': os.path.join(
                        DEFAULT_BACKLOG_PATH, transfer_name, directory, '.'),
                    'destination': os.path.join(
                        'watchedDirectories', 'SIPCreation',
                        'completedTransfers', transfer_name, directory, '.'),
                }
                if file_ not in files:
                    files.append(file_)

        logging.debug('copy_from_arrange_to_completed: files: %s', files)
        # Move files from backlog to local staging path
        (sip, error) = storage_service.get_files_from_backlog(files)

        if error is None:
            # Create SIP object
            error = create_arranged_sip(staging_sip_path, files)

        if error is None:
            # Update SIPArrange with in_SIP = True
            arrange.update(sip_created=True)
            # Remove directories
            models.SIPArrange.objects.filter(sip_created=False).filter(arrange_path__startswith=filepath).filter(original_path__isnull=True).delete()


    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'SIP created.'}

    return helpers.json_response(response)


def create_directory_within_arrange(request):
    """ Creates a directory entry in the SIPArrange table.

    path: GET parameter, path to directory in DEFAULT_ARRANGE_PATH to create
    """
    error = None
    
    path = base64.b64decode(request.POST.get('path', ''))

    if path:
        if path.startswith(DEFAULT_ARRANGE_PATH):
            models.SIPArrange.objects.create(
                original_path=None,
                arrange_path=os.path.join(path, ''), # ensure ends with /
                file_uuid=None,
            )
        else:
            error = 'Directory is not within the arrange directory.'

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'Creation successful.'}

    return helpers.json_response(response)

def move_within_arrange(request):
    """ Move files/folders within SIP Arrange.

    source path is in GET parameter 'filepath'
    destination path is in GET parameter 'destination'.

    If a source/destination path ends with / it is assumed to be a folder,
    otherwise it is assumed to be a file.
    """
    sourcepath = base64.b64decode(request.POST.get('filepath', ''))
    destination = base64.b64decode(request.POST.get('destination', ''))
    error = None

    logging.debug('Move within arrange: source: {}, destination: {}'.format(sourcepath, destination))

    if not (sourcepath.startswith(DEFAULT_ARRANGE_PATH) and destination.startswith(DEFAULT_ARRANGE_PATH)):
        error = '{} and {} must be inside {}'.format(sourcepath, destination, DEFAULT_ARRANGE_PATH)
    elif destination.endswith('/'):  # destination is a directory
        if sourcepath.endswith('/'):  # source is a directory
            folder_contents = models.SIPArrange.objects.filter(arrange_path__startswith=sourcepath)
            # Strip the last folder off sourcepath, but leave a trailing /, so
            # we retain the folder name when we move the files.
            source_parent = '/'.join(sourcepath.split('/')[:-2])+'/'
            for entry in folder_contents:
                entry.arrange_path = entry.arrange_path.replace(source_parent,destination,1)
                entry.save()
        else:  # source is a file
            models.SIPArrange.objects.filter(arrange_path=sourcepath).update(arrange_path=destination+os.path.basename(sourcepath))
    else:  # destination is a file (this should have been caught by JS)
        error = 'You cannot drag and drop onto a file.'

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'SIP files successfully moved.'}

    return helpers.json_response(response)

def _find_uuid_of_transfer_in_originals_directory_using_path(transfer_path):
    transfer_basename = transfer_path.replace(ORIGINAL_DIR, '').split('/')[1]

    # use lookup path to cleanly find UUID
    lookup_path = '%sharedPath%www/AIPsStore/transferBacklog/originals/' + transfer_basename + '/'
    cursor = connection.cursor()
    sql = 'SELECT unitUUID FROM transfersAndSIPs WHERE currentLocation=%s LIMIT 1'
    cursor.execute(sql, (lookup_path, ))
    possible_uuid_data = cursor.fetchone()

    # if UUID valid in system found, remove it
    if possible_uuid_data:
        return possible_uuid_data[0]
    else:
        return None


def _get_arrange_directory_tree(backlog_uuid, original_path, arrange_path):
    """ Fetches all the children of original_path from backlog_uuid and creates
    an identical tree in arrange_path.

    Helper function for copy_to_arrange.
    """
    # TODO Use ElasticSearch, since that's where we're getting the original info from now?  Could be easier to get file UUID that way
    ret = []
    browse = storage_service.browse_location(backlog_uuid, original_path)

    # Add everything that is not a directory (ie that is a file)
    entries = [e for e in browse['entries'] if e not in browse['directories']]
    for entry in entries:
        if entry not in ('processingMCP.xml'):
            path = os.path.join(original_path, entry)
            file_info = elasticSearchFunctions.get_transfer_file_info(
                'relative_path', path.replace(DEFAULT_BACKLOG_PATH, '', 1))
            file_uuid = file_info.get('fileuuid')
            transfer_uuid = file_info.get('sipuuid')
            ret.append(
                {'original_path': path,
                 'arrange_path': os.path.join(arrange_path, entry),
                 'file_uuid': file_uuid,
                 'transfer_uuid': transfer_uuid
                })

    # Add directories and recurse, adding their children too
    for directory in browse['directories']:
        original_dir = os.path.join(original_path, directory, '')
        arrange_dir = os.path.join(arrange_path, directory, '')
        # Don't fetch metadata or logs dirs
        # TODO only filter if the children of a SIP ie /arrange/sipname/metadata
        if not directory in ('metadata', 'logs'):
            ret.append({'original_path': None,
                        'arrange_path': arrange_dir,
                        'file_uuid': None,
                        'transfer_uuid': None})
            ret.extend(_get_arrange_directory_tree(backlog_uuid, original_dir, arrange_dir))

    return ret


def copy_to_arrange(request):
    """ Add files from backlog to in-progress SIPs being arranged.

    sourcepath: GET parameter, path relative to this pipelines backlog. Leading
        '/'s are stripped
    destination: GET parameter, path within arrange folder, should start with
        DEFAULT_ARRANGE_PATH ('/arrange/')
    """
    # Insert each file into the DB

    error = None
    sourcepath  = base64.b64decode(request.POST.get('filepath', '')).lstrip('/')
    destination = base64.b64decode(request.POST.get('destination', ''))
    logging.info('copy_to_arrange: sourcepath: {}'.format(sourcepath))
    logging.info('copy_to_arrange: destination: {}'.format(destination))

    # Lots of error checking:
    if not sourcepath or not destination:
        error = "GET parameter 'filepath' or 'destination' was blank."
    if not destination.startswith(DEFAULT_ARRANGE_PATH):
        error = '{} must be in arrange directory.'.format(destination)
    # If drop onto a file, drop it into its parent directory instead
    if not destination.endswith('/'):
        destination = os.path.dirname(destination)
    # Files cannot go into the top level folder
    if destination == DEFAULT_ARRANGE_PATH and not sourcepath.endswith('/'):
        error = '{} must go in a SIP, cannot be dropped onto {}'.format(
            sourcepath, DEFAULT_ARRANGE_PATH)

    # Create new SIPArrange entry for each object being copied over
    if not error:
        # IDEA memoize the backlog location?
        backlog_uuid = storage_service.get_location(purpose='BL')[0]['uuid']
        to_add = []

        # Construct the base arrange_path differently for files vs folders
        if sourcepath.endswith('/'):
            leaf_dir = sourcepath.split('/')[-2]
            # If dragging objects/ folder, actually move the contents of (not
            # the folder itself)
            if leaf_dir == 'objects':
                arrange_path = os.path.join(destination, '')
            else:
                # Strip UUID from transfer name
                uuid_regex = r'-[\w]{8}(-[\w]{4}){3}-[\w]{12}$'
                leaf_dir = re.sub(uuid_regex, '', leaf_dir)
                arrange_path = os.path.join(destination, leaf_dir) + '/'
                to_add.append({'original_path': None,
                   'arrange_path': arrange_path,
                   'file_uuid': None,
                   'transfer_uuid': None
                })
            to_add.extend(_get_arrange_directory_tree(backlog_uuid, sourcepath, arrange_path))
        else:
            arrange_path = os.path.join(destination, os.path.basename(sourcepath))
            file_info = elasticSearchFunctions.get_transfer_file_info(
                'relative_path', sourcepath.replace(DEFAULT_BACKLOG_PATH, '', 1))
            file_uuid = file_info.get('fileuuid')
            transfer_uuid = file_info.get('sipuuid')
            to_add.append({'original_path': sourcepath,
               'arrange_path': arrange_path,
               'file_uuid': file_uuid,
               'transfer_uuid': transfer_uuid
            })

        logging.info('copy_to_arrange: arrange_path: {}'.format(arrange_path))
        logging.debug('copy_to_arrange: files to be added: {}'.format(to_add))

        for entry in to_add:
            try:
                # TODO enforce uniqueness on arrange panel?
                models.SIPArrange.objects.create(
                    original_path=entry['original_path'],
                    arrange_path=entry['arrange_path'],
                    file_uuid=entry['file_uuid'],
                    transfer_uuid=entry['transfer_uuid'],
                )
            except IntegrityError:
                # FIXME Expecting this to catch duplicate original_paths, which
                # we want to ignore since a file can only be in one SIP.  Needs
                # to be updated not to ignore other classes of IntegrityErrors.
                logging.exception('Integrity error inserting: %s', entry)

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'Files added to the SIP.'}

    return helpers.json_response(response)


def download_ss(request):
    filepath = base64.b64decode(request.GET.get('filepath', '')).lstrip('/')
    logging.info('download filepath: %s', filepath)
    if not filepath.startswith(DEFAULT_BACKLOG_PATH):
        return django.http.HttpResponseBadRequest()
    filepath = filepath.replace(DEFAULT_BACKLOG_PATH, '', 1)

    # Get UUID
    uuid_regex = r'[\w]{8}(-[\w]{4}){3}-[\w]{12}'
    transfer_uuid = re.search(uuid_regex, filepath).group()

    # Get relative path
    # Find first /, should be at the end of the transfer name/uuid, rest is relative ptah
    relative_path = filepath[filepath.find('/')+1:]

    redirect_url = storage_service.extract_file_url(transfer_uuid, relative_path)
    return django.http.HttpResponseRedirect(redirect_url)

def download_fs(request):
    shared_dir = os.path.realpath(helpers.get_server_config_value('sharedDirectory'))
    filepath = base64.b64decode(request.GET.get('filepath', ''))
    requested_filepath = os.path.realpath('/' + filepath)

    # respond with 404 if a non-Archivematica file is requested
    try:
        if requested_filepath.index(shared_dir) == 0:
            return helpers.send_file(request, requested_filepath)
        else:
            raise django.http.Http404
    except ValueError:
        raise django.http.Http404

