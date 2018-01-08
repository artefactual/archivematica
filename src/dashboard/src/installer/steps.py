# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
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
import socket
import uuid

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
import requests
from tastypie.models import ApiKey

from main.models import Agent, User
import components.helpers as helpers
import storageService as storage_service
import utilities.FPRClient.client as FPRClient


logger = logging.getLogger('archivematica.dashboard')


def create_super_user(username, email, password, key):
    UserModel = get_user_model()
    # Create the new super user if it doesn't already exist
    try:
        user = UserModel._default_manager.get(**{UserModel.USERNAME_FIELD: username})
    except UserModel.DoesNotExist:
        # User doesn't exist, create it
        user = UserModel._default_manager.db_manager('default').create_superuser(username, email, password)
    # Create or update the user's api key
    api_key, created = ApiKey.objects.update_or_create(user=user, defaults={'key': key})


def set_agent_code(agent_code):
    archivematica_agent = Agent.objects.get(pk=1)
    archivematica_agent.identifiervalue = agent_code
    archivematica_agent.save()


def setup_pipeline(org_name, org_identifier):
    dashboard_uuid = helpers.get_setting('dashboard_uuid')
    # Setup pipeline only if dashboard_uuid doesn't already exists
    if dashboard_uuid:
        return
    # Assign UUID to Dashboard
    dashboard_uuid = str(uuid.uuid4())
    helpers.set_setting('dashboard_uuid', dashboard_uuid)

    # Update Archivematica version in DB
    set_agent_code(django_settings.AGENT_CODE)

    if org_name != '' or org_identifier != '':
        agent = get_agent()
        agent.name = org_name
        agent.identifiertype = 'repository code'
        agent.identifiervalue = org_identifier
        agent.save()


def submit_fpr_agent():
    agent = get_agent()
    url = django_settings.FPR_URL + 'agent/'
    resp = {}
    headers = {'Content-Type': 'application/json'}
    payload = {
        'uuid': helpers.get_setting('dashboard_uuid'),
        'agentType': 'new install',
        'agentName': agent.name,
        'clientIP': get_my_ip(),
        'agentIdentifierType': agent.identifiertype,
        'agentIdentifierValue': agent.identifiervalue
    }

    try:
        logger.info("FPR Server URL: {}".format(django_settings.FPR_URL))
        r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=django_settings.FPR_CLIENT_TIMEOUT, verify=True)
        if r.status_code == 201:
            resp['result'] = 'success'
        else:
            resp['result'] = 'failed to fetch from ' + url
    except:
        resp['result'] = 'failed to post to ' + url

    return resp


def download_fpr_rules():
    resp = {}
    logger.info("FPR Server URL: {}".format(django_settings.FPR_URL))
    fpr = FPRClient.FPRClient(django_settings.FPR_URL)
    resp['result'], resp['response'], error = fpr.getUpdates()
    if error:
        logging.warning("FPR update error: {}".format(error))
    return resp


def setup_pipeline_in_ss(use_default_config=False):
    # Check if pipeline is already registered on SS
    dashboard_uuid = helpers.get_setting('dashboard_uuid')
    try:
        storage_service.get_pipeline(dashboard_uuid)
    except Exception:
        logger.warning("SS inaccessible or pipeline not registered.")
    else:
        # If pipeline is already registered on SS, then exit
        logger.warning("This pipeline is already configured on SS.")
        return

    if not use_default_config:
        # Storage service manually set up, just register Pipeline if
        # possible. Do not provide additional information about the shared
        # path, or API, as this is probably being set up in the storage
        # service manually.
        storage_service.create_pipeline()
        return

    # Post first user & API key
    user = User.objects.all()[0]
    api_key = ApiKey.objects.get(user=user)

    # Create pipeline, tell it to use default setup
    storage_service.create_pipeline(
        create_default_locations=True,
        shared_path=django_settings.SHARED_DIRECTORY,
        api_username=user.username,
        api_key=api_key.key,
    )


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


def get_agent():
    return Agent.objects.get(pk=2)
