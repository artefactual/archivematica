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

from lxml import etree
import os
import sys

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render

from main import models
from components import helpers
from components.helpers import hidden_features

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
import storageService as storage_service

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

def index(request):
    file_path = os.path.join(
        helpers.get_server_config_value('sharedDirectory'),
        'sharedMicroServiceTasksConfigs/processingMCPConfigs/defaultProcessingMCP.xml'
    )

    # Lists of dicts declare what options to display, and where to look for
    # the options
    # Name: name in HTML
    # Label: text to display, <label> in HTML, required.  Fallback value for
    #   applies_to, lookup_description
    boolean_select_fields = [
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
            "yes_option": "Approve",
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

    # 'label': text to display, <label> in HTML.  Also, the
    # 'lookup_description': TasksConfig description to search against to find
    #   the MicroServiceChainLink for the
    #   MicroServiceChainChoice.choiceavailableatlink  If not specified, use label
    # 'link_uuid': If there are conflicts on lookup_description, specify this
    #   to use that MicroServiceChainLink
    chain_choice_fields = [
        {
            "name":  "create_sip",
            "label": "Create SIP(s)"
        },
        {
            "name":  "normalize",
            "label": "Normalize",
            "link_uuid": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
        },
        {
            "name":  "reminder",
            "label": "Reminder: add metadata if desired"
        }
    ]

    populate_select_fields_with_chain_choice_options(chain_choice_fields)

    # 'label': text to display, <label> in HTML.  Also, the
    # 'lookup_description': TasksConfig description to search against to find 
    #   the MicroServiceChainLink for the
    #   MicroServiceChainChoice.choiceavailableatlink  If not specified, use label
    # 'link_uuid': If there are conflicts on lookup_description, specify this
    #   to use that MicroServiceChainLink
    # 'applies_to': Description of the TasksConfig that the choice applies to.
    #   Put in defaultProcessingMCP.xml
    replace_dict_fields = [
        {
            "name": "select_format_id_tool_transfer",
            "label": "Select file format identification command (Transfer)",
            "link_uuid": 'f09847c2-ee51-429a-9478-a860477f6b8d',
            "applies_to": "Select file format identification command",
        },
        {
            "name": "select_format_id_tool_ingest",
            "label": "Select file format identification command (Ingest)",
            "link_uuid": '7a024896-c4f7-4808-a240-44c87c762bc5',
            "applies_to": "Select pre-normalize file format identification command",
        },
        {
            "name":  "compression_algo",
            "label": "Select compression algorithm"
        },
        {
            "name":  "compression_level",
            "label": "Select compression level"
        }
    ]

    """ Return a dict of AIP Storage Locations and their descriptions."""
    storage_directory_options = [{'value': '', 'label': '--Actions--'}]
    try:
        storage_directories = storage_service.get_location(purpose="AS")
        if storage_directories == None:
            raise Exception("Storage server improperly configured.")
    except Exception:
        messages.warning(request, 'Error retrieving AIP storage locations: is the storage server running? Please contact an administrator.')
    else:
        for storage_dir in storage_directories:
            storage_directory_options.append({
                'value': storage_dir['resource_uri'],
                'label': storage_dir['description']
            })
    other_fields = [
        {
            "name":    "store_aip_location",
            "label":   "Store AIP location",
            "options": storage_directory_options
        }
    ]

    populate_select_fields_with_replace_dict_options(replace_dict_fields)

    select_fields = chain_choice_fields + replace_dict_fields + other_fields

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
                str(float(quarantine_expiry) * (24 * 60 * 60))
            )

        # use select field submissions to add to XML
        for field in select_fields:
            enabled = request.POST.get(field['name'] + '_enabled')
            if enabled == 'yes':
                field_value = request.POST.get(field['name'], '')
                if field_value != '':
                    applies_to = field.get('applies_to', field['label'])
                    xmlChoices.add_choice(
                        applies_to,
                        field_value
                    )

        xmlChoices.write_to_file(file_path)

        messages.info(request, 'Saved!')

        return redirect('components.administration.views.processing')
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
                quarantine_expiry = float(choice.find('delay').text) / (24 * 60 * 60)

            # check select fields for defaults
            for field in select_fields:
                if applies_to == field['label'] or applies_to == field.get('applies_to', ""):
                    field['selected'] = go_to_chain
                    field['checked'] = 'checked'

    hide_features = hidden_features()
    return render(request, 'administration/processing.html', locals())

def lookup_chain_link(field):
    if 'link_uuid' in field:
        link = models.MicroServiceChainLink.objects.get(pk=field['link_uuid'])
    elif 'lookup_description' in field or 'label' in field:
        lookup_description = field.get('lookup_description', field['label'])
        task = models.TaskConfig.objects.get(description=lookup_description)
        link = models.MicroServiceChainLink.objects.get(currenttask=task.pk)

    return link

def remove_option_by_value(options, value):
    for option in options:
        if option['value'] == value:
            options.remove(option)

def populate_select_field_options_with_chain_choices(field):
    link = lookup_chain_link(field)

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
    link = lookup_chain_link(field)

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
