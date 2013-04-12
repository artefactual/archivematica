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
import sys, os
from lxml import etree
from components import helpers

class PreconfiguredChoices:
    xml     = None
    choices = None

    def __init__(self):
        self.xml = etree.Element('processingMCP')
        self.choices = etree.Element('preconfiguredChoices')

    def add_choice(self, applies_to_text, go_to_chain_text, delay_duration=None):
        choice = etree.Element('preconfiguredChoice')

        applies_to = etree.Element('appliesTo')
        applies_to.text = applies_to_text
        choice.append(applies_to)

        go_to_chain = etree.Element('goToChain')
        go_to_chain.text = go_to_chain_text
        choice.append(go_to_chain)

        if delay_duration != None:
            delay = etree.Element('delay', unitCtime='yes')
            delay.text = delay_duration
            choice.append(delay)

        self.choices.append(choice)

    def write_to_file(self, file_path):
        self.xml.append(self.choices)
        file = open(file_path, 'w')
        file.write(etree.tostring(self.xml, pretty_print=True))

def administration_processing(request):
    file_path = os.path.join(
        helpers.get_server_config_value('sharedDirectory'),
        'sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml'
    )

    boolean_select_fields = [
        {
            "name":       "backup_transfer",
            "label":      "Create transfer backup",
            "yes_option": "Backup transfer",
            "no_option":  "Do not backup transfer",
            "applies_to": "Workflow decision - create transfer backup"
        },
        {
            "name":       "quarantine_transfer",
            "label":      "Send transfer to quarantine",
            "yes_option": "Quarantine",
            "no_option":  "Skip quarantine",
            "applies_to": "Workflow decision - send transfer to quarantine"
        },
        {
            "name":       "normalize_transfer",
            "label":      "Approve normalization",
            "applies_to": "Approve normalization",
            "yes_option": "Approve normalization",
            "action":     "Approve"
        },
        {
            "name":       "store_aip",
            "label":      "Store AIP",
            "yes_option": "Store AIP",
            "applies_to": "Store AIP",
            "action":     "Store AIP"
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
        for field in boolean_select_fields:
            enabled = request.POST.get(field['name'])
            if enabled == 'yes':
                if 'yes_option' in field:
                    # can be set to either yes or no
                    toggle = request.POST.get(field['name'] + '_toggle', '')
                    if toggle == 'yes':
                        go_to_chain_text = field['yes_option']
                    elif 'no_option' in field:
                        go_to_chain_text = field['no_option']

                    if 'no_option' in field:
                        xmlChoices.add_choice(
                            field['applies_to'],
                            go_to_chain_text
                        )
                    else:
                        if toggle == 'yes':
                            xmlChoices.add_choice(
                                field['applies_to'],
                                go_to_chain_text
                            )
                else:
                    xmlChoices.add_choice(
                        field['label'],
                        field['action']
                    )

        # set quarantine duration if applicable
        quarantine_expiry_enabled = request.POST.get('quarantine_expiry_enabled', '')
        quarantine_expiry         = request.POST.get('quarantine_expiry', '')
        if quarantine_expiry_enabled == 'yes' and quarantine_expiry != '':
            xmlChoices.add_choice(
                'Remove from quarantine',
                'Unquarantine',
                quarantine_expiry
            )

        # use select field submissions to add to XML
        for field in select_fields:
            enabled = request.POST.get(field['name'] + '_enabled')
            if enabled == 'yes':
                field_value = request.POST.get(field['name'], '')
                if field_value != '':
                    xmlChoices.add_choice(
                        field['label'],
                        field_value
                    )

        xmlChoices.write_to_file(file_path)

        return HttpResponseRedirect(reverse('components.administration.views.administration_processing'))
    else:
        debug = request.GET.get('debug', '')
        quarantine_expiry = ''

        file = open(file_path, 'r')
        xml = file.read()

        # parse XML to work out locals()
        root = etree.fromstring(xml)
        choices = root.find('preconfiguredChoices')

        for item in boolean_select_fields:
            item['checked']     = ''
            item['yes_checked'] = ''
            item['no_checked']  = ''

        for choice in choices:
            applies_to = choice.find('appliesTo').text
            go_to_chain = choice.find('goToChain').text

            # use toggle field submissions to add to XML
            for field in boolean_select_fields:
                if applies_to == field['applies_to']:
                    set_field_property_by_name(boolean_select_fields, field['name'], 'checked', 'checked')

                    if 'yes_option' in field:
                        if go_to_chain == field['yes_option']:
                            set_field_property_by_name(boolean_select_fields, field['name'], 'yes_checked', 'selected')
                        else:
                            set_field_property_by_name(boolean_select_fields, field['name'], 'no_checked', 'selected')

            # a quarantine expiry was found
            if applies_to == 'Remove from quarantine':
                quarantine_expiry_enabled_checked = 'checked'
                quarantine_expiry = choice.find('delay').text

            # check select fields for defaults
            for field in select_fields:
                if applies_to == field['label']:
                    field['selected'] = go_to_chain
                    field['checked'] = 'checked'

    return render(request, 'administration/processing.html', locals())

def lookup_chain_link_by_description(field):
    try:
        lookup_description = field['lookup_description']
    except:
        lookup_description = field['label']

    if lookup_description == 'Normalize':
        # there are two task configs with the same description so we need to do more work
        tasks = models.TaskConfig.objects.filter(description=lookup_description)
        for task in tasks:
            link = models.MicroServiceChainLink.objects.get(currenttask=task.pk)
            choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink=link.pk)

            # look for the correct version
            if len(choices) > 3:
                return link
    else:
        task = models.TaskConfig.objects.filter(description=lookup_description)[0]
        link = models.MicroServiceChainLink.objects.get(currenttask=task.pk)

    return link

def remove_option_by_value(options, value):
    for option in options:
        if option['value'] == value:
            options.remove(option)

def populate_select_field_options_with_chain_choices(field):
    link = lookup_chain_link_by_description(field)

    choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink=link.pk)

    field['options'] = [{'value': '', 'label': '--Actions--'}]
    options = []
    for choice in choices:
        chain = models.MicroServiceChain.objects.get(pk=choice.chainavailable)
        option = {'value': chain.description, 'label': chain.description}
        options.append(option)

    if field['label'] == 'Create SIP(s)':
        remove_option_by_value(options, 'Reject transfer')
        remove_option_by_value(options, 'Create SIP(s) manually')

    if field['label'] == 'Normalize':
        remove_option_by_value(options, 'Reject SIP')

    options.sort()
    field['options'] += options

def populate_select_field_options_with_replace_dict_values(field):
    link = lookup_chain_link_by_description(field)

    replace_dicts = models.MicroServiceChoiceReplacementDic.objects.filter(
        choiceavailableatlink=link.pk
    )

    field['options'] = [{'value': '', 'label': '--Actions--'}]
    options = []
    for dict in replace_dicts:
        option = {'value': dict.description, 'label': dict.description}
        options.append(option)

    options.sort()
    field['options'] += options

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
