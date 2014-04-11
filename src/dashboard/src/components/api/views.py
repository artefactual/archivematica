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

import os, json
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.db.models import Q
from tastypie.authentication import ApiKeyAuthentication
from contrib.mcp.client import MCPClient
from main import models
from components import helpers

def authenticate_request(request):
    error = None

    api_auth = ApiKeyAuthentication()
    authorized = api_auth.is_authenticated(request)

    if authorized == True:
        client_ip = request.META['REMOTE_ADDR']
        whitelist = helpers.get_setting('api_whitelist', '127.0.0.1').split("\r\n")
        try:
            whitelist.index(client_ip)
            return
        except:
            error = 'Host/IP ' + client_ip + ' not authorized.'
    else:
        error = 'API key not valid.'

    return error

#
# Example: http://127.0.0.1/api/transfer/unapproved?username=mike&api_key=<API key>
#
def unapproved_transfers(request):
    if request.method == 'GET':
        auth_error = authenticate_request(request)

        response = {}

        if auth_error == None:
            message    = ''
            error      = None
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
                transfer_type = helpers.transfer_type_by_directory(transfer_watch_directory)

                job_directory = type_and_directory.replace(transfer_watch_directory + '/', '', 1)

                unapproved.append({
                    'type':      transfer_type,
                    'directory': job_directory
                })

            # get list of unapproved transfers
            # return list as JSON
            response['results'] = unapproved

            if error != None:
                response['message'] = error
                response['error']   = True
            else:
                response['message'] = 'Fetched unapproved transfers successfully.'

                if error != None:
                    return HttpResponseServerError(
                        json.dumps(response),
                        mimetype='application/json'
                    )
                else:
                    return helpers.json_response(response)
        else:
            response['message'] = auth_error
            response['error']   = True 
            return HttpResponseForbidden(
                json.dumps(response),
                mimetype='application/json'
            )
    else:
        return Http404

#
# Example: curl --data \
#   "username=mike&api_key=<API key>&directory=MyTransfer" \
#   http://127.0.0.1/api/transfer/approve
#
def approve_transfer(request):
    if request.method == 'POST':
        auth_error = authenticate_request(request)

        response = {}

        if auth_error == None:
            message = ''
            error   = None

            directory = request.POST.get('directory', '')
            type      = request.POST.get('type', 'standard')
            error     = approve_transfer_via_mcp(directory, type, request.user.id)

            if error != None:
                response['message'] = error
                response['error']   = True
            else:
                response['message'] = 'Approval successful.'

            if error != None:
                return HttpResponseServerError(
                    json.dumps(response),
                    mimetype='application/json'
                )
            else:
                return helpers.json_response(response)
        else:
            response['message'] = auth_error
            response['error']   = True
            return HttpResponseForbidden(
                json.dumps(response),
                mimetype='application/json'
            )
    else:
        raise Http404

def get_modified_standard_transfer_path(type=None):
    path = os.path.join(
        helpers.get_server_config_value('watchDirectoryPath'),
        'activeTransfers'
    )

    if type != None:
        try:
            path = os.path.join(path, helpers.transfer_directory_by_type(type))
        except:
            return None

    shared_directory_path = helpers.get_server_config_value('sharedDirectory')
    return path.replace(shared_directory_path, '%sharedPath%', 1)

def approve_transfer_via_mcp(directory, type, user_id):
    error = None

    if (directory != ''):
        # assemble transfer path
        modified_transfer_path = get_modified_standard_transfer_path(type)

        if modified_transfer_path == None:
            error = 'Invalid transfer type.'
        else:
            if type == 'zipped bag':
                transfer_path = os.path.join(modified_transfer_path, directory)
            else:
                transfer_path = os.path.join(modified_transfer_path, directory) + '/'

            # look up job UUID using transfer path
            try:
                job = models.Job.objects.filter(directory=transfer_path, currentstep='Awaiting decision')[0]

                type_task_config_descriptions = {
                    'standard':     'Approve standard transfer',
                    'unzipped bag': 'Approve bagit transfer',
                    'zipped bag':   'Approve zipped bagit transfer',
                    'dspace':       'Approve DSpace transfer',
                    'maildir':      'Approve maildir transfer',
                    'TRIM':         'Approve TRIM transfer'
                }

                type_description = type_task_config_descriptions[type]

                # use transfer type to fetch possible choices to execute
                task = models.TaskConfig.objects.get(description=type_description)
                link = models.MicroServiceChainLink.objects.get(currenttask=task.pk)
                choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink=link.pk)

                # attempt to find appropriate choice
                chain_to_execute = None
                for choice in choices:
                    if choice.chainavailable.description == 'Approve transfer':
                        chain_to_execute=choice.chainavailable.pk

                # execute choice if found
                if chain_to_execute != None:
                    client = MCPClient()

                    result = client.execute(job.pk, chain_to_execute, user_id)
                else:
                    error = 'Error: could not find MCP choice to execute.'

            except:
                error = 'Unable to find unapproved transfer directory.'

    else:
        error = 'Please specify a transfer directory.'

    return error
