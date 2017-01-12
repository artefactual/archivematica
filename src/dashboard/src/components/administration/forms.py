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

from __future__ import division

from collections import OrderedDict
import os
from lxml import etree

from django import forms
from django.conf import settings
from django.utils import six as django_six
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import TextInput, CheckboxInput, Select

from components import helpers
from main import models
import storageService as storage_service


class AgentForm(forms.ModelForm):
    class Meta:
        model = models.Agent
        fields = ('identifiervalue', 'name', 'agenttype')
        widgets = {
            'identifiervalue': TextInput(attrs=settings.INPUT_ATTRS),
            'name': TextInput(attrs=settings.INPUT_ATTRS),
            'agenttype': TextInput(attrs=settings.INPUT_ATTRS),
        }


class SettingsForm(forms.Form):
    """Base class form to save settings to DashboardSettings."""
    def save(self, *args, **kwargs):
        """Save all the form fields to the DashboardSettings table."""
        for key in self.cleaned_data:
            # Save the value
            helpers.set_setting(key, self.cleaned_data[key])


class StorageSettingsForm(SettingsForm):

    class StripCharField(forms.CharField):
        """
        Strip the value of leading and trailing whitespace.

        This won't be needed in Django 1.9, see
        https://docs.djangoproject.com/en/1.9/ref/forms/fields/#django.forms.CharField.strip.
        """
        def to_python(self, value):
            return super(forms.CharField, self).to_python(value).strip()

    storage_service_url = forms.URLField(
        label=_("Storage Service URL"),
        help_text=_('Full URL of the storage service. E.g. https://192.168.168.192:8000')
    )
    storage_service_user = forms.CharField(
        label=_('Storage Service User'),
        help_text=_('User in the storage service to authenticate as. E.g. test')
    )
    storage_service_apikey = StripCharField(
        label=_('API key'),
        help_text=_('API key of the storage service user. E.g. 45f7684483044809b2de045ba59dc876b11b9810')
    )
    storage_service_use_default_config = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Use default configuration'),
        help_text=_("You have to manually set up a custom configuration if the default configuration is not selected.")
    )


class ChecksumSettingsForm(SettingsForm):
    CHOICES = (
        ('md5', 'MD5'),
        ('sha1', 'SHA-1'),
        ('sha256', 'SHA-256'),
        ('sha512', 'SHA-512')
    )
    checksum_type = forms.ChoiceField(choices=CHOICES, label=_('Select algorithm'))


class TaxonomyTermForm(forms.ModelForm):
    class Meta:
        model = models.TaxonomyTerm
        fields = ('taxonomy', 'term')
        widgets = {
            "term": TextInput(attrs=settings.INPUT_ATTRS)
        }


class ProcessingConfigurationForm(forms.Form):
    """
    Build processing configuration form bounded to a processingMCP document.

    Every processing field in this form requires the following
    properties: type, name, label. In addition, these are some other
    constraints based on the type:

    - type = boolean
      Required: yes_option or no_option (or both)
    - type = chain_choice
      Optional: ignored_choices - list of choices that won't be presented to the user
      Optional: find_duplicates - persist choice across chain links with the same name
    - type = storage_service
      Required: purpose
    - type = days
      Required: chain
      Optional: placeholder, min_value
    """

    # The available processing fields indexed by choice_uuid.
    processing_fields = OrderedDict()

    # Workflow decision - send transfer to quarantine
    processing_fields['755b4177-c587-41a7-8c52-015277568302'] = {
        'type': 'boolean',
        'yes_option': '97ea7702-e4d5-48bc-b4b5-d15d897806ab',
        'no_option': 'd4404ab1-dc7f-4e9e-b1f8-aa861e766b8e',
    }
    # Remove from quarantine
    processing_fields['19adb668-b19a-4fcb-8938-f49d7485eaf3'] = {
        'type': 'days',
        'placeholder': _('days'),
        'chain': '333643b7-122a-4019-8bef-996443f3ecc5',
        'min_value': 0,
    }
    # Generate transfer structure report
    processing_fields['56eebd45-5600-4768-a8c2-ec0114555a3d'] = {
        'type': 'boolean',
        'yes_option': 'df54fec1-dae1-4ea6-8d17-a839ee7ac4a7',
        'no_option': 'e9eaef1e-c2e0-4e3b-b942-bfb537162795',
    }
    # Select file format identification command
    processing_fields['f09847c2-ee51-429a-9478-a860477f6b8d'] = {
        'type': 'replace_dict',
    }
    # Extract packages?
    processing_fields['dec97e3c-5598-4b99-b26e-f87a435a6b7f'] = {
        'type': 'chain_choice',
        'uuid': '01d80b27-4ad1-4bd1-8f8d-f819f18bf685',
    }
    # Delete package after extraction?
    processing_fields['f19926dd-8fb5-4c79-8ade-c83f61f55b40'] = {
        'type': 'replace_dict',
        'uuid': '85b1e45d-8f98-4cae-8336-72f40e12cbef',
    }
    # Examine contents?
    processing_fields['accea2bf-ba74-4a3a-bb97-614775c74459'] = {
        'type': 'chain_choice',
    }
    # Create SIP(s)
    processing_fields['bb194013-597c-4e4a-8493-b36d190f8717'] = {
        'type': 'chain_choice',
        'ignored_choices': ['Reject transfer'],
    }
    # Select pre-normalize file format identification command
    processing_fields['7a024896-c4f7-4808-a240-44c87c762bc5'] = {
        'type': 'replace_dict',
    }
    # Normalize
    processing_fields['cb8e5706-e73f-472f-ad9b-d1236af8095f'] = {
        'type': 'chain_choice',
        'ignored_choices': ['Reject SIP'],
        'find_duplicates': True,
    }
    # Approve normalization
    processing_fields['de909a42-c5b5-46e1-9985-c031b50e9d30'] = {
        'type': 'boolean',
        'yes_option': '1e0df175-d56d-450d-8bee-7df1dc7ae815',
    }
    # Reminder: add metadata if desired
    processing_fields['eeb23509-57e2-4529-8857-9d62525db048'] = {
        'type': 'chain_choice',
    }
    # Transcribe SIP contents
    processing_fields['7079be6d-3a25-41e6-a481-cee5f352fe6e'] = {
        'type': 'boolean',
        'yes_option': '5a9985d3-ce7e-4710-85c1-f74696770fa9',
        'no_option': '1170e555-cd4e-4b2f-a3d6-bfb09e8fcc53',
    }
    # Select file format identification command
    processing_fields['087d27be-c719-47d8-9bbb-9a7d8b609c44'] = {
        'type': 'replace_dict',
    }
    # Select compression algorithm
    processing_fields['01d64f58-8295-4b7b-9cab-8f1b153a504f'] = {
        'type': 'replace_dict',
    }
    # Select compression level
    processing_fields['01c651cb-c174-4ba4-b985-1d87a44d6754'] = {
        'type': 'replace_dict',
    }
    # Store AIP
    processing_fields['2d32235c-02d4-4686-88a6-96f4d6c7b1c3'] = {
        'type': 'boolean',
        'yes_option': '9efab23c-31dc-4cbd-a39d-bb1665460cbe',
    }
    # Store AIP location
    processing_fields['b320ce81-9982-408a-9502-097d0daa48fa'] = {
        'type': 'storage_service',
        'purpose': 'AS',
    }
    # Upload DIP
    processing_fields['92879a29-45bf-4f0b-ac43-e64474f0f2f9'] = {
        'type': 'chain_choice',
        'name': 'upload_dip',
        'label': 'Upload DIP',
        'ignored_choices': []
    }
    # Store DIP location
    processing_fields['b7a83da6-ed5a-47f7-a643-1e9f9f46e364'] = {
        'type': 'storage_service',
        'purpose': 'DS',
    }

    EMPTY_OPTION_NAME = _('None')
    EMPTY_CHOICES = [
        (None, EMPTY_OPTION_NAME),
    ]
    DEFAULT_FIELD_OPTS = {
        'required': False,
        'initial': None,
    }

    name = forms.RegexField(max_length=16, regex=r'^\w+$', required=True)
    name.widget.attrs['class'] = 'form-control'

    def __init__(self, *args, **kwargs):
        super(ProcessingConfigurationForm, self).__init__(*args, **kwargs)

        self.workflow = helpers.get_workflow_client().get_workflow('default')

        for choice_uuid, field in self.processing_fields.items():
            chain_link = self._get_link(choice_uuid)
            field['link'] = chain_link

            ftype = field['type']
            opts = self.DEFAULT_FIELD_OPTS.copy()
            opts['label'] = helpers.get_translation(chain_link.description)

            if ftype == 'days':
                if 'min_value' in field:
                    opts['min_value'] = field['min_value']
                self.fields[choice_uuid] = forms.IntegerField(**opts)
                if 'placeholder' in field:
                    self.fields[choice_uuid].widget.attrs['placeholder'] = field['placeholder']
                self.fields[choice_uuid].widget.attrs['class'] = 'form-control'

            else:
                choices = opts['choices'] = list(self.EMPTY_CHOICES)

                if ftype == 'boolean':
                    if 'yes_option' in field:
                        choices.append((field['yes_option'], _('Yes')))
                    if 'no_option' in field:
                        choices.append((field['no_option'], _('No')))

                elif ftype == 'chain_choice':
                    if chain_link is not None:
                        ignored_choices = field.get('ignored_choices', [])
                        for index, chain_uuid in enumerate(chain_link.config.userChoice.chainIds):
                            ch = self._get_chain(chain_uuid)
                            if ch is None:
                                continue
                            if ch.description['en'] in ignored_choices:
                                continue
                            choices.append((index, helpers.get_translation(ch.description)))

                elif ftype == 'replace_dict':
                    if chain_link is not None:
                        for item in chain_link.config.userChoiceDict.replacements:
                            choices.append((item.id, helpers.get_translation(item.description)))

                elif ftype == 'storage_service':
                    for loc in get_storage_locations(purpose=field['purpose']):
                        choices.append((loc['resource_uri'], loc['description']))

                self.fields[choice_uuid] = forms.ChoiceField(widget=Select(attrs={'class': 'form-control'}), **opts)

    def load_config(self, name):
        """
        Bound the choices found in the XML document to the form fields.
        """
        self.fields['name'].initial = name
        self.fields['name'].widget.attrs['readonly'] = 'readonly'

        config_path = os.path.join(helpers.processing_config_path(), '{}ProcessingMCP.xml'.format(name))
        root = etree.parse(config_path)
        for choice in root.findall('.//preconfiguredChoice'):
            applies_to = choice.findtext('appliesTo')
            go_to_chain = choice.findtext('goToChain')
            fprops = self.processing_fields.get(applies_to)
            field = self.fields.get(applies_to)
            if fprops is None or go_to_chain is None or field is None:
                continue
            if fprops['type'] == 'days':
                field.initial = int(float(choice.findtext('delay'))) // (24 * 60 * 60)
            elif fprops['type'] == 'chain_choice':
                for i, chain_id in enumerate(fprops['link'].config.userChoice.chainIds):
                    if chain_id == go_to_chain:
                        field.initial = i
                        continue
            else:
                field.initial = go_to_chain

    def save_config(self):
        """
        Encode the configuration to XML and write it to disk.
        """
        name = self.cleaned_data['name']
        del self.cleaned_data['name']
        config_path = os.path.join(helpers.processing_config_path(), '{}ProcessingMCP.xml'.format(name))
        config = PreconfiguredChoices()
        for choice_uuid, value in self.cleaned_data.items():
            fprops = self.processing_fields.get(choice_uuid)
            if fprops is None or value is None:
                continue
            field = self.fields.get(choice_uuid)
            if field is None:
                continue
            if isinstance(field, forms.ChoiceField):
                if not value:  # Ignore empty string!
                    continue
            if fprops['type'] == 'days':
                if value == 0:
                    continue
                delay = str(float(value) * (24 * 60 * 60))
                config.add_choice(choice_uuid, fprops['chain'], delay_duration=delay, comment=fprops['link'].description['en'])
            elif fprops['type'] == 'chain_choice':
                # value is going to be None, 0, 1, 2...
                try:
                    value = int(value)
                except ValueError:
                    continue
                link = fprops['link']
                chain_id = link.config.userChoice.chainIds[value]
                if fprops.get('find_duplicates', False):
                    chain = self._get_chain(chain_id)
                    if chain is None:
                        continue
                    link_desc = link.description['en']    # e.g. "Normalize"
                    chain_desc = chain.description['en']  # e.g. "Normalize for preservation"
                    for i, link_id in enumerate(self._get_duplicated_choices(link, chain_id)):
                        comment = '{} (match {} for "{}")'.format(link_desc, i + 1, chain_desc)
                        config.add_choice(link_id, chain_id, comment=comment)
                else:
                    config.add_choice(choice_uuid, chain_id, comment=link.description['en'])

            else:
                config.add_choice(choice_uuid, value, comment=fprops['link'].description['en'])
        config.save(config_path)

    def _get_link(self, uuid):
        return self.workflow.links.get(uuid, None)

    def _get_chain(self, uuid):
        return self.workflow.chains.get(uuid, None)

    def _get_duplicated_choices(self, link, chain_uuid):
        """
        Given a MicroServiceChainChoice link, return a full list of
        MicroServiceChainChoice links with the same description (e.g.
        "Normalize") and only if chain_uuid is a valid option for them.
        Not using dict.items() in PY2 to avoid slowness.
        """
        link_desc = link.description['en']
        link_ids = []
        for link_id, link in django_six.iteritems(self.workflow.links):
            if link.description['en'] != link_desc:
                continue
            if link.config.model != 'MicroServiceChainChoice':
                continue
            if chain_uuid not in link.config.userChoice.chainIds:
                continue
            link_ids.append(link_id)
        return link_ids


def get_storage_locations(purpose):
    try:
        dirs = storage_service.get_location(purpose=purpose)
        if len(dirs) == 0:
            raise Exception('Storage server improperly configured.')
    except Exception:
        dirs = []
    return dirs


class PreconfiguredChoices(object):
    """
    Encode processing configuration XML documents and optionally write to disk.
    """
    def __init__(self):
        self.xml = etree.Element('processingMCP')
        self.choices = etree.SubElement(self.xml, 'preconfiguredChoices')

    def add_choice(self, applies_to_text, go_to_chain_text, delay_duration=None, comment=None):
        if comment is not None:
            comment = etree.Comment(' {} '.format(comment))
            self.choices.append(comment)
        choice = etree.SubElement(self.choices, 'preconfiguredChoice')
        etree.SubElement(choice, 'appliesTo').text = applies_to_text
        etree.SubElement(choice, 'goToChain').text = go_to_chain_text
        if delay_duration is not None:
            etree.SubElement(choice, 'delay', {'unitCtime': 'yes'}).text = delay_duration

    def save(self, config_path):
        with open(config_path, 'w') as f:
            f.write(etree.tostring(self.xml, pretty_print=True))
