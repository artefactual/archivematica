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

from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.forms.widgets import TextInput, RadioSelect, CheckboxInput

from components import helpers
from main import models
from components.administration.models import ArchivistsToolkitConfig, ArchivesSpaceConfig

class AgentForm(forms.ModelForm):
    class Meta:
        model = models.Agent
        fields = ('identifiervalue', 'name')
        widgets = {
            'identifiervalue': TextInput(attrs=settings.INPUT_ATTRS),
            'name': TextInput(attrs=settings.INPUT_ATTRS),
        }

class SettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.reverse_checkboxes = kwargs.pop('reverse_checkboxes', [])
        super(SettingsForm, self).__init__(*args, **kwargs)

        for setting in self.reverse_checkboxes:
            # if it's enabled it shouldn't be checked and visa versa
            checked = not helpers.get_boolean_setting(setting)
            self.fields[setting] = forms.BooleanField(
                required=False,
                label=self.reverse_checkboxes[setting],
                initial=checked,
                widget=CheckboxInput()
            )

    def save(self, *args, **kwargs):
        """ Save each of the fields in the form to the Settings table. """
        for key in self.cleaned_data:
            # If it's one of the reverse_checkboxes, reverse the checkbox value
            if key in self.reverse_checkboxes:
                helpers.set_setting(key, not self.cleaned_data[key])
            # Otherwise, save the value
            else:
                helpers.set_setting(key, self.cleaned_data[key])


class StorageSettingsForm(SettingsForm):
    storage_service_url = forms.URLField(required=False,
        label="Full URL of the storage service")


class ArchivistsToolkitConfigForm(ModelForm):
    class Meta:
        model = ArchivistsToolkitConfig
        fields = ('host', 'port', 'dbname', 'dbuser', 'dbpass', 'atuser', 'premis', 'ead_actuate', 'ead_show', 'object_type', 'use_statement', 'uri_prefix', 'access_conditions', 'use_conditions')
        widgets = {
            'host': TextInput(attrs=settings.INPUT_ATTRS),
            'port': TextInput(attrs=settings.INPUT_ATTRS),
            'dbname': TextInput(attrs=settings.INPUT_ATTRS),
            'dbuser': TextInput(attrs=settings.INPUT_ATTRS),
            'dbpass': forms.PasswordInput(),
            'atuser': TextInput(attrs=settings.INPUT_ATTRS),
            'premis': RadioSelect(),
            'ead_actuate': RadioSelect(),
            'ead_show': RadioSelect(),
            'object_type': TextInput(attrs=settings.INPUT_ATTRS),
            'use_statement': TextInput(attrs=settings.INPUT_ATTRS),
            'uri_prefix': TextInput(attrs=settings.INPUT_ATTRS),
            'access_conditions': TextInput(attrs=settings.INPUT_ATTRS),
            'use_conditions': TextInput(attrs=settings.INPUT_ATTRS),
        }


class ArchivesSpaceConfigForm(ModelForm):
    class Meta:
        model = ArchivesSpaceConfig
        fields = ('host', 'port', 'user', 'passwd', 'premis', 'xlink_actuate', 'xlink_show', 'use_statement', 'object_type', 'access_conditions', 'use_conditions', 'uri_prefix', 'repository')
        widgets = {
            'host': TextInput(attrs=settings.INPUT_ATTRS),
            'port': TextInput(attrs=settings.INPUT_ATTRS),
            'user': TextInput(attrs=settings.INPUT_ATTRS),
            'passwd': forms.PasswordInput(),
            'premis': RadioSelect(),
            'xlink_actuate': RadioSelect(),
            'xlink_show': RadioSelect(),
            'use_statement': TextInput(attrs=settings.INPUT_ATTRS),
            'object_type': TextInput(attrs=settings.INPUT_ATTRS),
            'access_conditions': TextInput(attrs=settings.INPUT_ATTRS),
            'use_conditions': TextInput(attrs=settings.INPUT_ATTRS),
            'uri_prefix': TextInput(attrs=settings.INPUT_ATTRS),
            'repository': TextInput(attrs=settings.INPUT_ATTRS),
        }

class AtomDipUploadSettingsForm(SettingsForm):
    dip_upload_atom_url = forms.CharField(required=True,
        label="Upload URL",
        help_text="URL where the Qubit index.php frontend lives, SWORD services path will be appended.")
    dip_upload_atom_email = forms.CharField(required=True,
        label="Login email",
        help_text="E-mail account used to log into Qubit.")
    dip_upload_atom_password = forms.CharField(required=True,
        label="Login password",
        help_text="E-mail account used to log into Qubit.")
    dip_upload_atom_version = forms.ChoiceField(label="AtoM version",
        choices=((1, 'Atom 1.x'), (2, 'Atom 2.x')))
    dip_upload_atom_rsync_target = forms.CharField(required=False,
        label="Rsync target",
        help_text="The DIP can be sent with Rsync to a remote host before is deposited in Qubit. This is the destination value passed to Rsync (see man 1 rsync). For example: foobar.com:~/dips/.")
    dip_upload_atom_rsync_command = forms.CharField(required=False,
        label="Rsync command",
        help_text="If --rsync-target is used, you can use this argument to specify the remote shell manually. For example: ssh -p 22222 -l user.")
    dip_upload_atom_debug = forms.ChoiceField(required=False,
        label="Debug mode",
        help_text="Show additional details.",
        choices=((False, 'No'), (True, 'Yes')))

class TaxonomyTermForm(ModelForm):
    class Meta:
        model = models.TaxonomyTerm
        fields = ('taxonomy', 'term')
        widgets = {
            "term": TextInput(attrs=settings.INPUT_ATTRS)
        }
