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

import json
import logging
import requests_1_20 as requests
import socket
import sys
import urlparse
import uuid

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.shortcuts import redirect

from tastypie.models import ApiKey

import components.helpers as helpers
from components.administration.forms import StorageSettingsForm
from installer.forms import SuperUserCreationForm
from main.models import Agent
from components.administration.models import ArchivistsToolkitConfig

sys.path.append("/usr/lib/archivematica/archivematicaCommon/utilities")
import FPRClient.client as FPRClient
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import storageService as storage_service
import version

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

def welcome(request):
    # This form will be only accessible when the database has no users
    if 0 < User.objects.count():
        return redirect('main.views.home')
    # Form
    if request.method == 'POST':
        
        # assign UUID to dashboard
        dashboard_uuid = str(uuid.uuid4())
        helpers.set_setting('dashboard_uuid', dashboard_uuid)

        # Update Archivematica version in DB
        archivematica_agent = Agent.objects.get(pk=1)
        archivematica_agent.identifiervalue = "Archivematica-"+version.get_version()
        archivematica_agent.save()

        # create blank ATK DIP upload config
        config = ArchivistsToolkitConfig()
        config.save()

        # save organization PREMIS agent if supplied
        org_name       = request.POST.get('org_name', '')
        org_identifier = request.POST.get('org_identifier', '')

        if org_name != '' or org_identifier != '':
            agent = Agent.objects.get(pk=2)
            agent.name            = org_name
            agent.identifiertype  = 'repository code'
            agent.identifiervalue = org_identifier
            agent.save()

        # Save user and set cookie to indicate this is the first login
        form = SuperUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            api_key = ApiKey.objects.create(user=user)
            api_key.key = api_key.generate_key()
            api_key.save()
            user = authenticate(username=user.username, password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                request.session['first_login'] = True
                return redirect('installer.views.fprconnect')
    else:
        form = SuperUserCreationForm()

    return render(request, 'installer/welcome.html', {
        'form': form,
      })

def get_my_ip():
    server_addr = '1.2.3.4'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect((server_addr, 9))
        client = s.getsockname()[0]
    except socket.error:
        client = "1.1.1.1"
    finally:
        del s
    return client
    
def fprconnect(request):
    if request.method == 'POST':
        return redirect('installer.views.storagesetup')
    else:
        return render(request, 'installer/fprconnect.html')

def fprupload(request):
    response_data = {} 
    agent = Agent.objects.get(pk=2)
    #url = 'https://fpr.archivematica.org/fpr/api/v2/agent/'
    url = django_settings.FPR_URL + 'agent/'
    logging.info("FPR Server URL: {}".format(django_settings.FPR_URL))
    payload = {'uuid': helpers.get_setting('dashboard_uuid'), 
               'agentType': 'new install', 
               'agentName': agent.name, 
               'clientIP': get_my_ip(), 
               'agentIdentifierType': agent.identifiertype, 
               'agentIdentifierValue': agent.identifiervalue
              }
    headers = {'Content-Type': 'application/json'}
    try: 
        r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10, verify=True)
        if r.status_code == 201:
            response_data['result'] = 'success'
        else:
            response_data['result'] = 'failed to fetch from ' + url
    except:
        response_data['result'] = 'failed to post to ' + url   

    return helpers.json_response(response_data) 

def fprdownload(request):
    response_data = {}

    fprserver = django_settings.FPR_URL
    logging.info("FPR Server URL: {}".format(fprserver))
    fpr = FPRClient.FPRClient(fprserver)
    (response_data['result'], response_data['response'], error) = fpr.getUpdates()
    if error:
        logging.warning("FPR update error: {}".format(error))

    return helpers.json_response(response_data)
 
def storagesetup(request):
    # Display the dashboard UUID on the storage service setup page
    dashboard_uuid = helpers.get_setting('dashboard_uuid', None)
    assert dashboard_uuid is not None
    # Prefill the storage service URL
    inital_data = {'storage_service_url':
        helpers.get_setting('storage_service_url', 'http://localhost:8000')}
    storage_form = StorageSettingsForm(request.POST or None, initial=inital_data)
    if storage_form.is_valid():
        # Set storage service URL
        storage_form.save()
        if "use_default" in request.POST:
            shared_path = helpers.get_server_config_value('sharedDirectory')
            # Post first user & API key
            user = User.objects.all()[0]
            api_key = ApiKey.objects.get(user=user)
            # Create pipeline, tell it to use default setup
            try:
                storage_service.create_pipeline(
                    create_default_locations=True,
                    shared_path=shared_path,
                    api_username=user.username,
                    api_key=api_key.key,
                )
            except Exception:
                messages.warning(request, 'Error creating pipeline: is the storage server running? Please contact an administrator.')
            else:
                # Add the storage service URL to the API whitelist
                ss_url = urlparse.urlparse(helpers.get_setting('storage_service_url'))
                whitelist = helpers.get_setting('api_whitelist', '127.0.0.1')
                whitelist = '\n'.join([whitelist, ss_url.hostname])
                helpers.set_setting('api_whitelist', whitelist)
        else:
            # Storage service manually set up, just register Pipeline if
            # possible. Do not provide additional information about the shared
            # path, or API, as this is probably being set up in the storage
            # service manually.
            try:
                storage_service.create_pipeline()
            except Exception:
                pass
        return redirect('main.views.home')
    else:
        return render(request, 'installer/storagesetup.html', locals())
