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
from django.forms.widgets import TextInput, Textarea, CheckboxInput

from components import helpers
from main import models

class AdministrationForm(forms.Form):
    arguments = forms.CharField(required=False, widget=Textarea(attrs=settings.TEXTAREA_ATTRS))

class AgentForm(forms.ModelForm):
    identifiervalue = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))
    name = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))

    class Meta:
        model = models.Agent
        exclude = ('identifiertype')


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
