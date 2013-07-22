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

from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from main import forms
from main import models
import logging
import sys
import components.administration.views_processing as processing_views
from lxml import etree
from components.administration.forms import AdministrationForm
from components.administration.forms import AgentForm
from components.administration.forms import ToggleSettingsForm
import components.decorators as decorators
import components.helpers as helpers
import storageService as storage_service


logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematica.log", 
    level=logging.INFO)

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def administration(request):
    return HttpResponseRedirect(reverse('components.administration.views.sources'))

def administration_dip(request):
    upload_setting = models.StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    hide_features = helpers.hidden_features()
    return render(request, 'administration/dip.html', locals())

def dip_edit(request, id):
    if request.method == 'POST':
        upload_setting = models.StandardTaskConfig.objects.get(pk=id)
        form = AdministrationForm(request.POST)
        if form.is_valid():
            upload_setting.arguments = form.cleaned_data['arguments']
            upload_setting.save()

    return HttpResponseRedirect(reverse("components.administration.views.administration_dip"))

def atom_dips(request):
    link_id = atom_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = dips_formset()

    valid_submission, formset = dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    hide_features = helpers.hidden_features()
    return render(request, 'administration/dips_edit.html', locals())

def contentdm_dips(request):
    link_id = contentdm_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = dips_formset()

    valid_submission, formset, add_form = dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    hide_features = helpers.hidden_features()
    return render(request, 'administration/dips_contentdm_edit.html', locals())

def atom_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select DIP upload destination')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def contentdm_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select target CONTENTdm server')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def dips_formset():
    return modelformset_factory(
        models.MicroServiceChoiceReplacementDic,
        form=forms.MicroServiceChoiceReplacementDicForm,
        extra=0,
        can_delete=True
    )

def dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet):
    valid_submission = True
    formset = None

    add_form = forms.MicroServiceChoiceReplacementDicForm()

    if request.method == 'POST':
        # if any new configuration data has been submitted, attempt to add it
        if request.POST.get('description', '') != '' or request.POST.get('replacementdic', '') != '':
            postData = request.POST.copy()
            postData['choiceavailableatlink'] = link_id

            add_form = forms.MicroServiceChoiceReplacementDicForm(postData)

            if add_form.is_valid():
                choice = models.MicroServiceChoiceReplacementDic()
                choice.choiceavailableatlink = link_id
                choice.description           = request.POST.get('description', '')
                choice.replacementdic        = request.POST.get('replacementdic', '')
                choice.save()

                # create new blank field
                add_form = forms.MicroServiceChoiceReplacementDicForm()

        formset = ReplaceDirChoiceFormSet(request.POST)

        # take note of formset validity because if submission was successful
        # we reload it to reflect
        # deletions, etc.
        valid_submission = formset.is_valid()

        if valid_submission:
            # save/delete partial data (without association with specific link)
            instances = formset.save()

            # restore link association
            for instance in instances:
                instance.choiceavailableatlink = link_id
                instance.save()
    return valid_submission, formset, add_form

def storage(request):
    picker_js_file = 'storage_directory_picker.js'
    system_directory_description = 'AIP storage'
    hide_features = helpers.hidden_features()
    return render(request, 'administration/sources.html', locals())

def storage_json(request):
    return administration_system_directory_data_request_handler(
      request,
      "AS",
    )

def sources(request):
    picker_js_file = 'source_directory_picker.js'
    system_directory_description = 'Transfer source'
    hide_features = helpers.hidden_features()
    return render(request, 'administration/sources.html', locals())

def sources_json(request):
    return administration_system_directory_data_request_handler(
      request,
      "TS",
    )

def administration_system_directory_data_request_handler(request, purpose, access_protocol="FS"):
    message = ''
    if request.method == 'POST':
        # TODO This should be passed in by the view
        space = storage_service.get_space(access_protocol="FS", path="/")[0]
        path = request.POST.get('path', '')
        if path != '':
            if storage_service.get_location(path=path,
                                    purpose=purpose,
                                    space=space):
                message = 'Directory already added.'
            elif storage_service.create_location(path=path,
                                         purpose=purpose):
                message = 'Directory added.'
            else:
                message = 'Error adding directory.'
        else:
            message = 'Path is empty.'
        logging.debug("Message: {}".format(message))
        if purpose == "AS":
            administration_render_storage_directories_to_dicts()

    directories = storage_service.get_location(purpose=purpose)

    response = {}
    response['message'] = message
    response['directories'] = directories

    return HttpResponse(
      simplejson.JSONEncoder().encode(response),
      mimetype='application/json'
    )

def storage_delete_json(request, id):
    response = system_directory_delete_request_handler(
      request,
      "AS",
      id
    )
    administration_render_storage_directories_to_dicts()
    return response

def sources_delete_json(request, id):
    return system_directory_delete_request_handler(
      request, 
      "TS",
      id
    )

def system_directory_delete_request_handler(request, purpose, uuid):
    if storage_service.delete_location(uuid):
        message = 'Deleted.'
    else:
        logging.warning("Failed to delete directory {}, purpose {}".format(
            uuid, purpose))
        message = 'Failed to delete directory.'

    if purpose == "AS":
        administration_render_storage_directories_to_dicts()
    response = {}
    response['message'] = message
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def processing(request):
    return processing_views.index(request)

def administration_render_storage_directories_to_dicts():
    administration_flush_aip_storage_dicts()
    storage_directories = storage_service.get_location(purpose="AS")
    logging.debug("Storage Directories: {}".format(storage_directories))
    link_pk = administration_get_aip_storage_link_pk()
    for d in storage_directories:
        dict = models.MicroServiceChoiceReplacementDic()
        dict.choiceavailableatlink = link_pk
        dict.description = d['description']
        dict.replacementdic = '{{"%AIPsStore%": "{}"}}'.format(d['resource_uri'])
        dict.save()

def administration_flush_aip_storage_dicts():
    link_pk = administration_get_aip_storage_link_pk()
    entries = models.MicroServiceChoiceReplacementDic.objects.filter(
      choiceavailableatlink=link_pk
    )
    for entry in entries:
        entry.delete()

def administration_get_aip_storage_link_pk():
    tasks = models.TaskConfig.objects.filter(description='Store AIP location')
    links = models.MicroServiceChainLink.objects.filter(currenttask=tasks[0].pk)
    return links[0].pk

def premis_agent(request):
    agent = models.Agent.objects.get(pk=2)
    if request.POST:
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
    else:
        form = AgentForm(instance=agent)

    hide_features = helpers.hidden_features()
    return render(request, 'administration/premis_agent.html', locals())

def api(request):
    if request.method == 'POST':
        whitelist = request.POST.get('whitelist', '')
        helpers.set_setting('api_whitelist', whitelist)
    else:
        whitelist = helpers.get_setting('api_whitelist', '127.0.0.1')

    hide_features = helpers.hidden_features()
    return render(request, 'administration/api.html', locals())

def general(request):
    dashboard_uuid = helpers.get_setting('dashboard_uuid')

    toggleableSettings = [
      {'dashboard_administration_atom_dip_enabled': 'Hide AtoM DIP upload link'},
      {'dashboard_administration_contentdm_dip_enabled': 'Hide CONTENTdm DIP upload link'},
      {'dashboard_administration_dspace_enabled': 'Hide DSpace transfer type'},
    ]

    if request.method == 'POST':
        for setting in toggleableSettings:
            name = setting.keys()[0]
            if request.POST.get(name) == 'on':
                setting = True
            else:
                setting = False

            # settings indicate whether or not something is enabled so if we want
            # do disable it we do a boolean not
            setting = not setting

            helpers.set_setting(name, setting)

    form = ToggleSettingsForm(extra=toggleableSettings)

    hide_features = helpers.hidden_features()
    return render(request, 'administration/general.html', locals())
