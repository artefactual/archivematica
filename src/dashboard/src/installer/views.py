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

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _
from tastypie.models import ApiKey

import components.helpers as helpers
from components.administration.forms import StorageSettingsForm
from installer.forms import OrganizationForm, SuperUserCreationForm
from installer.steps import download_fpr_rules, setup_pipeline, setup_pipeline_in_ss, submit_fpr_agent


def welcome(request):
    # This form will be only accessible when there is no uuid
    dashboard_uuid = helpers.get_setting('dashboard_uuid')
    if dashboard_uuid:
        return redirect('main.views.home')

    # Do we need to set up a user?
    set_up_user = not User.objects.exists()

    if request.method == 'POST':
        # save organization PREMIS agent if supplied
        setup_pipeline(
            org_name=request.POST.get('org_name', ''),
            org_identifier=request.POST.get('org_identifier', '')
        )

        if set_up_user:
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
            request.session['first_login'] = True
            return redirect('installer.views.fprconnect')
    else:
        form = SuperUserCreationForm() if set_up_user else OrganizationForm()

    return render(request, 'installer/welcome.html', {
        'form': form,
    })


def fprconnect(request):
    if request.method == 'POST':
        return redirect('installer.views.storagesetup')
    else:
        return render(request, 'installer/fprconnect.html')


def fprupload(request):
    return helpers.json_response(submit_fpr_agent())


def fprdownload(request):
    return helpers.json_response(download_fpr_rules())


def storagesetup(request):
    # Display the dashboard UUID on the storage service setup page
    dashboard_uuid = helpers.get_setting('dashboard_uuid', None)
    assert dashboard_uuid is not None

    # Prefill the storage service URL
    inital_data = {
        'storage_service_url': helpers.get_setting('storage_service_url', 'http://localhost:8000'),
        'storage_service_user': helpers.get_setting('storage_service_user', 'test'),
        'storage_service_apikey': helpers.get_setting('storage_service_apikey', None)
    }
    storage_form = StorageSettingsForm(request.POST or None, initial=inital_data)
    if not storage_form.is_valid():
        return render(request, 'installer/storagesetup.html', locals())
    storage_form.save()

    try:
        use_default_config = storage_form.cleaned_data['storage_service_use_default_config']
        setup_pipeline_in_ss(use_default_config)
    except Exception:
        messages.warning(request, _('Error creating pipeline: is the storage server running? Please contact an administrator.'))

    return redirect('main.views.home')
