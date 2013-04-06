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

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from main.models import Agent
from installer.forms import SuperUserCreationForm
from installer.forms import FPRConnectForm
from tastypie.models import ApiKey
import json
import requests

def welcome(request):
    # This form will be only accessible when the database has no users
    if 0 < User.objects.count():
      return HttpResponseRedirect(reverse('main.views.home'))
    # Form
    if request.method == 'POST':
        # save organization PREMIS agent if supplied
        org_name       = request.POST.get('org_name', '')
        org_identifier = request.POST.get('org_identifier', '')

        if org_name != '' or org_identifier != '':
            agent = Agent.objects.get(pk=2)
            agent.name            = org_name
            agent.identifiertype  = 'organization'
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
              return HttpResponseRedirect(reverse('installer.views.fprconnect'))
    else:
        form = SuperUserCreationForm()

    return render(request, 'installer/welcome.html', {
        'form': form,
      })

def fprconnect(request):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('main.views.home'))
    else:
        return render(request, 'installer/fprconnect.html')

def fprupload(request):
    response_data = {} 
    agent = Agent.objects.get(pk=2)
    url = 'http://fpr.archivematica.org:8000/fpr/api/v1/Agent/'
    payload = {'uuid': '3b66a42d-7109-495b-8234-89aa8bc533c5', 
               'agentType': 'new install', 
               'agentName': agent.name, 
               'clientIP': '1.1.1.1', 
               'agentIdentifierType': agent.identifiertype, 
               'agentIdentifierValue': agent.identifiervalue
              }
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    if r.status_code == 201:
        response_data['result'] = 'success'
    else:
        response_data['result'] = 'failed'
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")            

def fprdownload(request):
    response_data = {}
    response_data['result'] = 'success'
    return HttpResponse(json.dumps(response_data), content_type="application/json")
