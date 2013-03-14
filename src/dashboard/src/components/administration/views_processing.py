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
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from main import models
import sys, os, ConfigParser
from lxml import etree

class PreconfiguredChoices:
    xml     = None
    choices = None

    def __init__(self):
        self.xml = etree.Element('processingMCP')
        self.choices = etree.Element('preconfiguredChoices')

    def add_choice(self, applies_to_text, go_to_chain_text):
        choice = etree.Element('preconfiguredChoice')

        applies_to = etree.Element('appliesTo')
        applies_to.text = applies_to_text
        choice.append(applies_to)

        go_to_chain = etree.Element('goToChain')
        go_to_chain.text = go_to_chain_text
        choice.append(go_to_chain)

        self.choices.append(choice)

    def write_to_file(self, file_path):
        self.xml.append(self.choices)
        file = open(file_path, 'w')
        file.write(etree.tostring(self.xml, pretty_print=True))

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
            "yes_option":   "Quarantine",
            "no_option":    "Skip quarantine",
            "applies_to": "Workflow decision - send transfer to quarantine"
        },
        {
            "name":  "normalize_transfer",
            "label": "Approve normalization",
            "applies_to": "Approve normalization",
            "action": "Approve"
        },
        {
            "name":  "store_aip",
            "label": "Store AIP",
            "applies_to": "Store AIP",
            "action": "Store AIP"
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
        xmlChoices = PreconfiguredChoices()

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

                    xmlChoices.add_choice(
                        field['applies_to'],
                        go_to_chain_text
                    )
                else:
                    xmlChoices.add_choice(
                        field['label'],
                        field['action']
                    )

        # use select field submissions to add to XML
        for field in select_fields:
            field_value = request.POST.get(field['name'], '')
            if field_value != '':
                xmlChoices.add_choice(
                    field['label'],
                    field_value
                )

        xmlChoices.write_to_file(file_path)

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

def populate_select_field_options_with_replace_dict_values(field):
    link = lookup_chain_link_by_description(field)

    replace_dicts = models.MicroServiceChoiceReplacementDic.objects.filter(
        choiceavailableatlink=link.pk
    )

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

def set_field_property_by_name(fields, name, property, value):
    for field in fields:
        if field['name'] == name:
            field[property] = value
