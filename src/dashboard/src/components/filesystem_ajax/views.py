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
import os
import logging
import shutil
import sys
import tempfile
import uuid

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.db import connection

from components import helpers
import components.ingest.helpers as ingest_helpers
import components.filesystem_ajax.helpers as filesystem_ajax_helpers
from main import models

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import databaseFunctions
import elasticSearchFunctions
from archivematicaCreateStructuredDirectory import createStructuredDirectory
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
COMPLETED_TRANSFERS_DIR = SHARED_DIRECTORY_ROOT + '/watchedDirectories/SIPCreation/completedTransfers'
ORIGINAL_DIR            = SHARED_DIRECTORY_ROOT + '/www/AIPsStore/transferBacklog/originals'


def directory_children_proxy_to_storage_server(request, location_uuid, basePath=False):
    path = ''
    if (basePath):
        path = base64.b64decode(basePath)
    path = path + base64.b64decode(request.GET.get('base_path', ''))
    path = path + base64.b64decode(request.GET.get('path', ''))
    path = base64.b64encode(path)

    response = storage_service.browse_location(location_uuid, path)

    return helpers.json_response(response)

def contents(request):
    path = request.GET.get('path', '/home')
    response = filesystem_ajax_helpers.directory_to_dict(path)
    return helpers.json_response(response)

def arrange_contents(request):
    base_path = request.GET.get('path', '/arrange/')

    # Must indicate that base_path is a folder by ending with /
    if base_path and not base_path.endswith('/'):
        base_path += '/'

    # Query SIP Arrangement for results
    # Get all the paths that are not in SIPs and start with base_path.  We don't
    # need the objects, just the arrange_path
    paths = models.SIPArrange.objects.filter(sip_created=False).filter(arrange_path__startswith=base_path).order_by('arrange_path').values_list('arrange_path', flat=True)

    # Convert the response into an entries [] and directories []
    # 'entries' contains everything (files and directories)
    response = {'entries': [], 'directories': []}
    for path in paths:
        # Stip common prefix
        if path.startswith(base_path):
            path = path[len(base_path):]
        entry = path.split('/', 1)[0]
        # Only insert once
        if entry and entry not in response['entries']:
            response['entries'].append(entry)
            if path.endswith('/'):  # path is a dir
                response['directories'].append(entry)

    return helpers.json_response(response)


def originals_contents(request):
    path = request.GET.get('path', '/home')
    response = filesystem_ajax_helpers.directory_to_dict(path)
    for child in response['children']:
        # check if name has uuid and, if so, check if it's valid
        possible_uuid = child['name'][-36:]
        if len(possible_uuid) == 36:
            try:
                transfer = models.Transfer.objects.get(uuid=possible_uuid)
                data = {'transfer_uuid': possible_uuid}
                if transfer.accessionid != None:
                    data['accessionId'] = transfer.accessionid
                child['data'] = data
            except:
                pass
    return helpers.json_response(response)

def delete(request):
    filepath = request.POST.get('filepath', '')
    filepath = os.path.join('/', filepath)
    error = filesystem_ajax_helpers.check_filepath_exists(filepath)

    if error == None:
        filepath = os.path.join(filepath)
        if os.path.isdir(filepath):
            try:
                shutil.rmtree(filepath)
            except:
                error = 'Error attempting to delete directory.'
        else:
            os.remove(filepath)

    response = {}

    # if deleting from originals, delete ES data as well
    if ORIGINAL_DIR in filepath and filepath.index(ORIGINAL_DIR) == 0:
        transfer_uuid = _find_uuid_of_transfer_in_originals_directory_using_path(filepath)
        if transfer_uuid != None:
            elasticSearchFunctions.connect_and_remove_backlog_transfer_files(transfer_uuid)

    if error != None:
      response['message'] = error
      response['error']   = True
    else:
      response['message'] = 'Delete successful.'

    return helpers.json_response(response)

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
    paths = request.POST.getlist('paths[]', '')
    paths = [base64.b64decode(path) for path in paths]

    # Create temp directory that everything will be copied into
    temp_base_dir = helpers.get_client_config_value('temp_dir') or None
    temp_dir = tempfile.mkdtemp(dir=temp_base_dir)

    for i, path in enumerate(paths):
        target = transfer_name + '_' + str(i + 1)
        copy_transfer_component(transfer_name=target,
                                path=path, destination=temp_dir)

        if helpers.file_is_an_archive(path):
            filepath = os.path.join(temp_dir, os.path.basename(path))
        else:
            filepath = os.path.join(temp_dir, target)
        copy_to_start_transfer(filepath=filepath,
                               type=transfer_type, accession=accession)

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

def copy_to_start_transfer(filepath='', type='', accession=''):
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
        if accession != '':
            temp_uuid = uuid.uuid4().__str__()
            mcp_destination = destination.replace(SHARED_DIRECTORY_ROOT + '/', '%sharedPath%') + '/'
            transfer = models.Transfer.objects.create(
                uuid=temp_uuid,
                accessionid=accession,
                currentlocation=mcp_destination
            )
            transfer.save()

        try:
            shutil.move(filepath, destination)
        except:
            error = 'Error copying from ' + filepath + ' to ' + destination + '. (' + str(sys.exc_info()[0]) + ')'

    if error:
        raise Exception(error)

def copy_to_originals(request):
    filepath = request.POST.get('filepath', '')
    error = filesystem_ajax_helpers.check_filepath_exists('/' + filepath)

    if error == None:
        processingDirectory = '/var/archivematica/sharedDirectory/currentlyProcessing/'
        sipName = os.path.basename(filepath)
        autoProcessSIPDirectory = '/var/archivematica/sharedDirectory/watchedDirectories/SIPCreation/SIPsUnderConstruction/'
        tmpSIPDir = os.path.join(processingDirectory, sipName) + "/"
        destSIPDir =  os.path.join(autoProcessSIPDirectory, sipName) + "/"

        sipUUID = uuid.uuid4().__str__()

        createStructuredDirectory(tmpSIPDir)
        databaseFunctions.createSIP(destSIPDir.replace('/var/archivematica/sharedDirectory/', '%sharedPath%'), sipUUID)

        objectsDirectory = os.path.join('/', filepath, 'objects')

        #move the objects to the SIPDir
        for item in os.listdir(objectsDirectory):
            shutil.move(os.path.join(objectsDirectory, item), os.path.join(tmpSIPDir, "objects", item))

        #moveSIPTo autoProcessSIPDirectory
        shutil.move(tmpSIPDir, destSIPDir)

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copy successful.'

    return helpers.json_response(response)

def copy_from_arrange_to_completed(request):
    filepath = '/' + request.POST.get('filepath', '')

    if filepath != '':
        ingest_helpers.initiate_sip_from_files_structured_like_a_completed_transfer(filepath)

    #return copy_to_originals(request)

def create_directory_within_arrange(request):
    error = None
    
    path = request.POST.get('path', '')

    if path != '':
        absolute_path = os.path.join('/', path)
        if _within_arrange_dir(absolute_path):
            os.mkdir(absolute_path)
        else:
            error = 'Directory is not within the arrange directory.'

    response = {}

    response['message'] = absolute_path
    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Creation successful.'

    return helpers.json_response(response)

def move_within_arrange(request):
    sourcepath  = request.POST.get('filepath', '')
    destination = request.POST.get('destination', '')

    error = filesystem_ajax_helpers.check_filepath_exists('/' + sourcepath)

    if error == None:
        # TODO: make sure within arrange
        basename = os.path.basename('/' + sourcepath)
        destination_full = os.path.join('/', destination, basename)
        if (os.path.exists(destination_full)):
            error = 'A file or directory named ' + basename + ' already exists at this path.'
        else:
            shutil.move('/' + sourcepath, destination_full)

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copy successful.'

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

def _arrange_dir():
    return os.path.realpath(os.path.join(
        helpers.get_client_config_value('sharedDirectoryMounted'),
        'arrange'))

def _within_arrange_dir(path):
    arrange_dir = _arrange_dir()
    real_path = os.path.realpath(path)
    return arrange_dir in real_path and real_path.index(arrange_dir) == 0

def copy_to_arrange(request):
    arrange_dir = _arrange_dir()

    # TODO: limit sourcepath to certain allowable locations
    sourcepath  = request.POST.get('filepath', '')
    destination = request.POST.get('destination', '')

    # make source and destination path absolute
    sourcepath = os.path.join('/', sourcepath)
    destination = os.path.realpath(os.path.join('/', destination))

    # work out relative path within originals folder
    originals_subpath = sourcepath.replace(ORIGINAL_DIR, '')

    # work out transfer directory level and source transfer directory
    transfer_directory_level = originals_subpath.count('/')
    source_transfer_directory = originals_subpath.split('/')[1]

    error = filesystem_ajax_helpers.check_filepath_exists(sourcepath)

    if error == None:
        uuid = _find_uuid_of_transfer_in_originals_directory_using_path(os.path.join(ORIGINAL_DIR, source_transfer_directory))

        if uuid != None:
            # remove UUID from destination directory name
            modified_basename = os.path.basename(sourcepath).replace('-' + uuid, '')
        else:
            # TODO: should return error?
            modified_basename = os.path.basename(sourcepath)

        # confine destination to subdir of arrange
        if _within_arrange_dir(destination):
            full_destination = os.path.join(destination, modified_basename)
            full_destination = helpers.pad_destination_filepath_if_it_already_exists(full_destination)

            if os.path.isdir(sourcepath):
                try:
                    shutil.copytree(
                        sourcepath,
                        full_destination
                    )
                except:
                    error = 'Error copying from ' + sourcepath + ' to ' + full_destination + '.'

                if error == None:
                    # remove any metadata and logs folders
                    for path in filesystem_ajax_helpers.directory_contents(full_destination):
                        basename = os.path.basename(path)
                        if basename == 'metadata' or basename == 'logs':
                            if os.path.isdir(path):
                                shutil.rmtree(path)

            else:
                shutil.copy(sourcepath, full_destination)

            # if the source path isn't a whole transfer folder, then
            # copy the source transfer's METS file into the objects
            # folder of the destination... if there is not objects
            # folder then return an error

            arrange_subpath = full_destination.replace(arrange_dir, '')
            dest_transfer_directory = arrange_subpath.split('/')[1]

            _add_copied_files_to_arrange_log(sourcepath, full_destination)

            # an entire transfer isn't being copied... copy in METS if
            # it doesn't exist
            if transfer_directory_level != 1 and uuid != None:
                # work out location of METS file in source transfer
                source_mets_path = os.path.join(ORIGINAL_DIR, source_transfer_directory, 'metadata/submissionDocumentation/METS.xml')

                # work out destination object folder
                objects_directory = os.path.join(arrange_dir, dest_transfer_directory, 'objects')
                destination_mets = os.path.join(objects_directory, 'METS-' + uuid + '.xml')
                if not os.path.exists(destination_mets):
                    shutil.copy(source_mets_path, destination_mets)

            # log all files copied to arrange.log
            #f
        else:
            error = 'The destination {} is not within the arrange directory ({}).'.format(destination, arrange_dir)

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copy successful.'

    return helpers.json_response(response)

def _add_copied_files_to_arrange_log(sourcepath, full_destination):
    arrange_dir = _arrange_dir()

    # work out relative path within originals folder
    originals_subpath = sourcepath.replace(ORIGINAL_DIR, '')

    arrange_subpath = full_destination.replace(arrange_dir, '')
    dest_transfer_directory = arrange_subpath.split('/')[1]

    # add to arrange log
    transfer_logs_directory = os.path.join(arrange_dir, dest_transfer_directory, 'logs')
    if not os.path.exists(transfer_logs_directory):
        os.mkdir(transfer_logs_directory)
    arrange_log_filepath = os.path.join(transfer_logs_directory, 'arrange.log')
    transfer_root = os.path.join(arrange_dir, dest_transfer_directory)
    with open(arrange_log_filepath, "a") as logfile:
        if os.path.isdir(full_destination):
            # recursively add all files to arrange log 
            for dirname, dirnames, filenames in os.walk(full_destination):
                # print path to all filenames.
                for filename in filenames:
                    filepath = os.path.join(dirname, filename).replace(transfer_root, '')
                    relative_path_to_file_within_source_dir = '/'.join(filepath.split('/')[3:])
                    original_filepath = os.path.join(
                        originals_subpath[1:],
                        relative_path_to_file_within_source_dir
                    )
                    log_entry = original_filepath + ' -> ' + filepath.replace(transfer_root, '')[1:] + "\n"
                    logfile.write(log_entry)
        else:
            log_entry = originals_subpath[1:] + ' -> ' + full_destination.replace(transfer_root, '')[1:] + "\n"
            logfile.write(log_entry)

def download(request):
    shared_dir = os.path.realpath(helpers.get_client_config_value('sharedDirectoryMounted'))
    filepath = base64.b64decode(request.GET.get('filepath', ''))
    requested_filepath = os.path.realpath('/' + filepath)

    # respond with 404 if a non-Archivematica file is requested
    try:
        if requested_filepath.index(shared_dir) == 0:
            return helpers.send_file(request, requested_filepath)
        else:
            raise Http404
    except ValueError:
        raise Http404
