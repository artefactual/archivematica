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
from django.template import RequestContext
from main import forms
from main import models
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
from django.contrib.auth.decorators import user_passes_test
import urllib
from components.administration.forms import AdministrationForm
from components.administration.forms import AgentForm
import components.decorators as decorators
import components.helpers as helpers

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Administration
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

def administration(request):
    return HttpResponseRedirect(reverse('components.administration.views.administration_sources'))

def administration_dip(request):
    upload_setting = models.StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    return render(request, 'administration/dip.html', locals())

def administration_dip_edit(request, id):
    if request.method == 'POST':
        upload_setting = models.StandardTaskConfig.objects.get(pk=id)
        form = AdministrationForm(request.POST)
        if form.is_valid():
            upload_setting.arguments = form.cleaned_data['arguments']
            upload_setting.save()

    return HttpResponseRedirect(reverse("components.administration.views.administration_dip"))

def administration_atom_dips(request):
    link_id = administration_atom_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'administration/dips_edit.html', locals())

def administration_contentdm_dips(request):
    link_id = administration_contentdm_dip_destination_select_link_id()
    ReplaceDirChoices = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link_id)

    ReplaceDirChoiceFormSet = administration_dips_formset()

    valid_submission, formset, add_form = administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet)

    if request.method != 'POST' or valid_submission:
        formset = ReplaceDirChoiceFormSet(queryset=ReplaceDirChoices)

    return render(request, 'administration/dips_contentdm_edit.html', locals())

def administration_atom_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select DIP upload destination')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_contentdm_dip_destination_select_link_id():
    taskconfigs = models.TaskConfig.objects.filter(description='Select target CONTENTdm server')
    taskconfig = taskconfigs[0]
    links = models.MicroServiceChainLink.objects.filter(currenttask=taskconfig.id)
    link = links[0]
    return link.id

def administration_dips_formset():
    return modelformset_factory(
        models.MicroServiceChoiceReplacementDic,
        form=forms.MicroServiceChoiceReplacementDicForm,
        extra=0,
        can_delete=True
    )

def administration_dips_handle_updates(request, link_id, ReplaceDirChoiceFormSet):
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

def administration_storage(request):
    picker_js_file = 'storage_directory_picker.js'
    system_directory_description = 'AIP storage'
    return render(request, 'administration/sources.html', locals())

def administration_storage_json(request):
    return administration_system_directory_data_request_handler(
      request,
      models.StorageDirectory
    )

def administration_sources(request):
    picker_js_file = 'source_directory_picker.js'
    system_directory_description = 'Transfer source'
    return render(request, 'administration/sources.html', locals())

def administration_sources_json(request):
    return administration_system_directory_data_request_handler(
      request,
      models.SourceDirectory
    )

def administration_system_directory_data_request_handler(request, model):
    message = ''
    if request.method == 'POST':
         path = request.POST.get('path', '')
         if path != '':
             try:
                 model.objects.get(path=path)
             except model.DoesNotExist:
                 # save dir
                 source_dir = model()
                 source_dir.path = path
                 source_dir.save()
                 message = 'Directory added.'
             else:
                 message = 'Directory already added.'
         else:
             message = 'Path is empty.'
         if model == models.StorageDirectory:
             administration_render_storage_directories_to_dicts()

    response = {}
    response['message'] = message
    response['directories'] = []

    for directory in model.objects.all():
      response['directories'].append({
        'id':   directory.id,
        'path': directory.path
      })

    return HttpResponse(
      simplejson.JSONEncoder().encode(response),
      mimetype='application/json'
    )

def administration_storage_delete_json(request, id):
    response = administration_system_directory_delete_request_handler(
      request,
      models.StorageDirectory,
      id
    )
    administration_render_storage_directories_to_dicts()
    return response

def administration_sources_delete_json(request, id):
    return administration_system_directory_delete_request_handler(
      request, 
      models.SourceDirectory,
      id
    )

def administration_system_directory_delete_request_handler(request, model, id):
    model.objects.get(pk=id).delete()
    if model == models.StorageDirectory:
        administration_render_storage_directories_to_dicts()
    response = {}
    response['message'] = 'Deleted.'
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def administration_processing(request):
    file_path = '/var/archivematica/sharedDirectory/sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml'

    if request.method == 'POST':
        xml = request.POST.get('xml', '')
        file = open(file_path, 'w')
        file.write(xml)
    else:
        file = open(file_path, 'r')
        xml = file.read()

    return render(request, 'administration/processing.html', locals())

def administration_render_storage_directories_to_dicts():
    administration_flush_aip_storage_dicts()
    storage_directories = models.StorageDirectory.objects.all()
    link_pk = administration_get_aip_storage_link_pk()
    for dir in storage_directories:
        dict = models.MicroServiceChoiceReplacementDic()
        dict.choiceavailableatlink = link_pk
        if dir.path == '%sharedPath%www/AIPsStore/':
            description = 'Store AIP in standard Archivematica Directory'
        else:
            description = dir.path
        dict.description = description
        dict.replacementdic = '{"%AIPsStore%":"' + dir.path + '/"}'
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

def administration_premis_agent(request):
    agent = models.Agent.objects.get(pk=2)
    if request.POST:
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
    else:
        form = AgentForm(instance=agent)

    return render(request, 'administration/premis_agent.html', locals())

def administration_api(request):
    if request.method == 'POST':
        whitelist = request.POST.get('whitelist', '')
        helpers.set_setting('api_whitelist', whitelist)
    else:
        whitelist = helpers.get_setting('api_whitelist', '127.0.0.1')

    return render(request, 'administration/api.html', locals())
