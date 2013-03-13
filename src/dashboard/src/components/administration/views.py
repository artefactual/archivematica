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
import sys, os, ConfigParser
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")
import pyes
from django.contrib.auth.decorators import user_passes_test
import urllib
from lxml import etree
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

def add_choice_to_choices(choices, applies_to_text, go_to_chain_text):
    choice = etree.Element('preconfiguredChoice')

    applies_to = etree.Element('appliesTo')
    applies_to.text = applies_to_text
    choice.append(applies_to)

    go_to_chain = etree.Element('goToChain')
    go_to_chain.text = go_to_chain_text
    choice.append(go_to_chain)

    choices.append(choice)

def administration_system_directory_delete_request_handler(request, model, id):
    model.objects.get(pk=id).delete()
    if model == models.StorageDirectory:
        administration_render_storage_directories_to_dicts()
    response = {}
    response['message'] = 'Deleted.'
    return HttpResponse(simplejson.JSONEncoder().encode(response), mimetype='application/json')

def lookup_chain_link_by_description(field):
    try:
        lookup_description = field['lookup_description']
    except:
        lookup_description = field['label']

    task = models.TaskConfig.objects.filter(description=lookup_description)[0]
    link = models.MicroServiceChainLink.objects.get(currenttask=task.pk)

    return link

def populate_select_field_options_with_chain_choices(field):
    link = lookup_chain_link_by_description(field)

    choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink=link.pk)

    field['options'] = [{'value': '', 'label': '--Actions--'}]
    for choice in choices:
        chain = models.MicroServiceChain.objects.get(pk=choice.chainavailable)
        option = {'value': chain.description, 'label': chain.description}
        field['options'].append(option)

# use this somewhere
def set_field_property_by_name(fields, name, property, value):
    for field in fields:
        if field['name'] == name:
            field[property] = value

def populate_select_field_options_with_replace_dict_values(field):
    link = lookup_chain_link_by_description(field)

    replace_dicts = models.MicroServiceChoiceReplacementDic.objects.filter(choiceavailableatlink=link.pk)

    field['options'] = [{'value': '', 'label': '--Actions--'}]
    for dict in replace_dicts:
        option = {'value': dict.description, 'label': dict.description}
        field['options'].append(option)

def populate_select_fields_with_chain_choice_options(fields):
    for field in fields:
        populate_select_field_options_with_chain_choices(field)

def populate_select_fields_with_replace_dict_options(fields):
    for field in fields:
        populate_select_field_options_with_replace_dict_values(field)

def administration_processing(request):
    clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)
    shared_directory = config.get('MCPClient', "sharedDirectoryMounted")
    file_path = os.path.join(shared_directory, 'sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml')

    optional_radio_fields = [
        {
            "name":         "backup_transfer",
            "label":        "Create transfer backup",
            "yes_option":   "Backup transfer",
            "no_option":    "Do not backup transfer",
            "applies_to": "Workflow decision - create transfer backup"
        },
        {
            "name":         "quarantine_transfer",
            "label":        "Send transfer to quarantine",
            "yes_option":   "Quarantine transfer",
            "no_option":    "Skip quarantine",
            "applies_to": "Workflow decision - send transfer to quarantine"
        },
        {
            "name":  "normalize_transfer",
            "label": "Approve normalization",
            "applies_to": "Approve normalization"
        },
        {
            "name":  "store_aip",
            "label": "Store AIP",
            "applies_to": "Store AIP"
        }
    ]

    chain_choice_fields = [
        {
            "name":  "create_sip",
            "label": "Create SIP(s)"
        },
        {
            "name":  "select_format_id_tool",
            "label": "Select format identification tool"
        },
        {
            "name":  "normalize",
            "label": "Normalize"
        }
    ]

    populate_select_fields_with_chain_choice_options(chain_choice_fields)

    replace_dict_fields = [
        {
            "name":  "compression_algo",
            "label": "Select compression algorithm"
        },
        {
            "name":  "compression_level",
            "label": "Select compression level"
        },
        {
            "name":  "store_aip_location",
            "label": "Store AIP location"
        }
    ]

    populate_select_fields_with_replace_dict_options(replace_dict_fields)

    select_fields = chain_choice_fields + replace_dict_fields

    if request.method == 'POST':
        # render XML using request data
        xml = etree.Element('processingMCP')
        choices = etree.Element('preconfiguredChoices')
        xml.append(choices)

        # use toggle field submissions to add to XML
        for field in optional_radio_fields:
            enabled = request.POST.get(field['name'])
            if enabled == 'yes':
                if 'yes_option' in field:
                    # can be set to either yes or no
                    toggle = request.POST.get(field['name'] + '_toggle', '')
                    if toggle == 'yes':
                        go_to_chain_text = field['yes_option']
                    else:
                        go_to_chain_text = field['no_option']

                    add_choice_to_choices(
                        choices,
                        field['applies_to'],
                        go_to_chain_text
                    )
                else:
                    add_choice_to_choices(
                        choices,
                        field['label'],
                        field['label']
                    )

        # use select field submissions to add to XML
        for field in select_fields:
            field_value = request.POST.get(field['name'], '')
            if field_value != '':
                add_choice_to_choices(
                    choices,
                    field['label'],
                    field_value
                )

        xml.append(choices)

        file = open(file_path, 'w')
        file.write(etree.tostring(xml, pretty_print=True))

        return HttpResponseRedirect(reverse('components.administration.views.administration_processing'))
    else:
        quarantine_expiry = ''

        file = open(file_path, 'r')
        xml = file.read()

        # parse XML to work out locals()
        root = etree.fromstring(xml)
        choices = root.find('preconfiguredChoices')

        for item in optional_radio_fields:
            item['checked']     = ''
            item['yes_checked'] = ''
            item['no_checked']  = ''

        for choice in choices:
            applies_to = choice.find('appliesTo').text
            go_to_chain = choice.find('goToChain').text

            # use toggle field submissions to add to XML
            for field in optional_radio_fields:
                if applies_to == field['applies_to']:
                    set_field_property_by_name(optional_radio_fields, field['name'], 'checked', 'checked')

                    if 'yes_option' in field:
                        if go_to_chain == field['yes_option']:
                            set_field_property_by_name(optional_radio_fields, field['name'], 'yes_checked', 'checked')
                        else:
                            set_field_property_by_name(optional_radio_fields, field['name'], 'no_checked', 'checked')

            # a quarantine expiry was found
            if applies_to == 'Remove from quarantine':
                quarantine_expiry = '2'

            # check select fields for defaults
            for field in select_fields:
                if applies_to == field['label']:
                    field['selected'] = go_to_chain

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
