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
    file_path = helpers.default_processing_config_path()

    # Lists of dicts declare what options to display, and where to look for
    # the options
    # name: Value of the `name` attribute in the <input> HTML element
    # choice_uuid: UUID of the microservice chainlink at which the choice occurs
    # label: Human-readable label to be displayed to the user
    # yes_option and no_option: UUIDs for the yes and no choice chains, respectively
    boolean_select_fields = [
        {
            "name":         "quarantine_transfer",
            "choice_uuid":  "755b4177-c587-41a7-8c52-015277568302", # Workflow decision - send transfer to quarantine
            "label":        "Send transfer to quarantine",
            "yes_option":   "97ea7702-e4d5-48bc-b4b5-d15d897806ab", # Quarantine
            "no_option":    "d4404ab1-dc7f-4e9e-b1f8-aa861e766b8e" # Skip quarantine
        },
        {
            "name":         "normalize_transfer",
            "choice_uuid":  "de909a42-c5b5-46e1-9985-c031b50e9d30",
            "label":        "Approve normalization",
            "yes_option":   "1e0df175-d56d-450d-8bee-7df1dc7ae815", # Approve
            "action":       "Approve"
        },
        {
            "name":         "store_aip",
            "choice_uuid":  "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
            "label":        "Store AIP",
            "yes_option":   "9efab23c-31dc-4cbd-a39d-bb1665460cbe", # Store AIP
            "action":       "Store AIP"
        },
        {
            "name":         "transcribe_file",
            "choice_uuid":  "7079be6d-3a25-41e6-a481-cee5f352fe6e",
            "label":        "Transcribe files (OCR)",
            "yes_option":   "5a9985d3-ce7e-4710-85c1-f74696770fa9",
            "no_option":    "1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53",
        },
        {
            "name":         "tree",
            "choice_uuid":  "56eebd45-5600-4768-a8c2-ec0114555a3d",
            "label":        "Generate transfer structure report",
            "yes_option":   "df54fec1-dae1-4ea6-8d17-a839ee7ac4a7", # Generate transfer structure report
            "no_option":    "e9eaef1e-c2e0-4e3b-b942-bfb537162795",
            "action":       "Generate transfer structure report"
        },
    ]

    # name: Value of the `name` attribute in the <input> HTML element
    # label: Human-readable label to be displayed to the user
    # choice_uuid: UUID of the microservice chainlink at which the choice occurs
    chain_choice_fields = [
        {
            "name":  "create_sip",
            "label": "Create SIP(s)",
            "choice_uuid": "bb194013-597c-4e4a-8493-b36d190f8717"
        },
        {
            "name":  "extract_packages",
            "label": "Extract packages",
            "choice_uuid": "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
            "uuid": "01d80b27-4ad1-4bd1-8f8d-f819f18bf685"
        },
        {
            "name":  "normalize",
            "label": "Normalize",
            "choice_uuid": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
        },
        {
            "name":  "reminder",
            "label": "Reminder: add metadata if desired",
            "choice_uuid": "eeb23509-57e2-4529-8857-9d62525db048",
        },
        {
            "name":  "examine",
            "label": "Examine contents",
            "choice_uuid": "accea2bf-ba74-4a3a-bb97-614775c74459"
        },
    ]

    populate_select_fields_with_chain_choice_options(chain_choice_fields)

    # name: Value of the `name` attribute in the <input> HTML element
    # choice_uuid: UUID of the microservice chainlink at which the choice occurs
    replace_dict_fields = [
        {
            "name": "select_format_id_tool_transfer",
            "label": "Select file format identification command (Transfer)",
            "choice_uuid": 'f09847c2-ee51-429a-9478-a860477f6b8d'
        },
        {
            "name": "select_format_id_tool_ingest",
            "label": "Select file format identification command (Ingest)",
            "choice_uuid": '7a024896-c4f7-4808-a240-44c87c762bc5'
        },
        {
            "name": "select_format_id_tool_submissiondocs",
            "label": "Select file format identification command (Submission documentation & metadata)",
            "choice_uuid": '087d27be-c719-47d8-9bbb-9a7d8b609c44'
        },
        {
            "name":  "delete_packages",
            "label": "Delete packages after extraction",
            "choice_uuid": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
            "uuid": "85b1e45d-8f98-4cae-8336-72f40e12cbef"
        },
        {
            "name":  "compression_algo",
            "label": "Select compression algorithm",
            "choice_uuid": "01d64f58-8295-4b7b-9cab-8f1b153a504f"
        },
        {
            "name":  "compression_level",
            "label": "Select compression level",
            "choice_uuid": "01c651cb-c174-4ba4-b985-1d87a44d6754"
        }
    ]

    def storage_dir_cb(storage_dir):
        return {
            'value': storage_dir['resource_uri'],
            'label': storage_dir['description']
        }

    """ Return a dict of AIP Storage Locations and their descriptions."""
    storage_directory_options = [{'value': '', 'label': '--Actions--'}]
    dip_directory_options = [{'value': '', 'label': '--Actions--'}]
    try:
        storage_directories = storage_service.get_location(purpose="AS")
        dip_directories = storage_service.get_location(purpose="DS")
        if None in (storage_directories, dip_directories):
            raise Exception("Storage server improperly configured.")
    except Exception:
        messages.warning(request, 'Error retrieving AIP/DIP storage locations: is the storage server running? Please contact an administrator.')
    else:
        storage_directory_options += [storage_dir_cb(d) for d in storage_directories]
        dip_directory_options += [storage_dir_cb(d) for d in dip_directories]

    storage_service_options = [
        {
            "name":          "store_aip_location",
            "label":         "Store AIP location",
            "choice_uuid":   "b320ce81-9982-408a-9502-097d0daa48fa",
            "options":       storage_directory_options,
            # Unlike other options, the correct value here is a literal string,
            # not a pointer to a chain or dict in the database.
            "do_not_lookup": True
        },
        {
            "name":          "store_dip_location",
            "label":         "Store DIP location",
            "choice_uuid":   "b7a83da6-ed5a-47f7-a643-1e9f9f46e364",
            "options":       dip_directory_options,
            # Unlike other options, the correct value here is a literal string,
            # not a pointer to a chain or dict in the database.
            "do_not_lookup": True
        }
    ]

    populate_select_fields_with_replace_dict_options(replace_dict_fields)

    select_fields = chain_choice_fields + replace_dict_fields + storage_service_options

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
                            field['choice_uuid'],
                            go_to_chain_text
                        )
                    else:
                        if toggle == 'yes':
                            xmlChoices.add_choice(
                                field['choice_uuid'],
                                go_to_chain_text
                            )

        # set quarantine duration if applicable
        quarantine_expiry_enabled = request.POST.get('quarantine_expiry_enabled', '')
        quarantine_expiry         = request.POST.get('quarantine_expiry', '')
        if quarantine_expiry_enabled == 'yes' and quarantine_expiry != '':
            xmlChoices.add_choice(
                '19adb668-b19a-4fcb-8938-f49d7485eaf3', # Remove from quarantine
                '333643b7-122a-4019-8bef-996443f3ecc5', # Unquarantine
                str(float(quarantine_expiry) * (24 * 60 * 60))
            )

        # use select field submissions to add to XML
        for field in select_fields:
            enabled = request.POST.get(field['name'] + '_enabled')
            if enabled == 'yes':
                field_value = request.POST.get(field['name'], '')
                if field_value != '':
                    if field.get('do_not_lookup', False):
                        target = field_value
                    else:
                        target = uuid_from_description(field_value, field['choice_uuid'])

                    xmlChoices.add_choice(
                        field['choice_uuid'],
                        target
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
        choices = root.findall('.//preconfiguredChoice')

        for item in boolean_select_fields:
            item['checked']     = ''
            item['yes_checked'] = ''
            item['no_checked']  = ''

        for choice in choices:
            applies_to = choice.find('appliesTo').text
            go_to_chain = choice.find('goToChain').text

            # use toggle field submissions to add to XML
            for field in boolean_select_fields:
                if applies_to == field['choice_uuid']:
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
                if applies_to == field['choice_uuid'] and go_to_chain:
                    try:
                        chain = models.MicroServiceChain.objects.get(pk=go_to_chain)
                        choice = chain.description
                    except models.MicroServiceChain.DoesNotExist:
                        try:
                            choice = models.MicroServiceChoiceReplacementDic.objects.get(pk=go_to_chain).description
                        except models.MicroServiceChoiceReplacementDic.DoesNotExist:
                            # fallback for storage service options, which are
                            # strings that don't map to chains or dicts in
                            # the database
                            choice = go_to_chain

                    field['selected'] = choice
                    field['checked'] = 'checked'

    hide_features = hidden_features()
    return render(request, 'administration/processing.html', locals())

def lookup_chain_link(field):
    return models.MicroServiceChainLink.objects.get(pk=field['choice_uuid'])

def remove_option_by_value(options, value):
    for option in options:
        if option['value'] == value:
            options.remove(option)

def uuid_from_description(description, choice):
    """
    Attempts to fetch the UUID of either a MicroServiceChain or a
    MicroServiceChoiceReplacementDic that matches the provided description.

    "choice" is the pk of the choice with which the option is associated;
    it will be used when looking up a replacement dict in order to ensure the
    result is associated with the correct choice.
    """
    try:
        choice = models.MicroServiceChainChoice.objects.get(choiceavailableatlink_id=choice,
            chainavailable__description=description)
        return choice.chainavailable.pk
    except models.MicroServiceChainChoice.DoesNotExist:
        return models.MicroServiceChoiceReplacementDic.objects.filter(description=description, choiceavailableatlink=choice)[0].pk

def populate_select_field_options_with_chain_choices(field):
    link = lookup_chain_link(field)

    choices = models.MicroServiceChainChoice.objects.filter(choiceavailableatlink_id=link.pk)

    field['options'] = [{'value': '', 'label': '--Actions--'}]
    options = []
    for choice in choices:
        chain = choice.chainavailable
        option = {'value': chain.description, 'label': chain.description}
        options.append(option)

    if field['label'] == 'Create SIP(s)':
        remove_option_by_value(options, 'Reject transfer')

    if field['label'] == 'Normalize':
        remove_option_by_value(options, 'Reject SIP')

    options.sort()
    field['options'] += options

def populate_select_field_options_with_replace_dict_values(field):
    link = lookup_chain_link(field)

    replace_dicts = models.MicroServiceChoiceReplacementDic.objects.filter(
        choiceavailableatlink_id=link.pk
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
