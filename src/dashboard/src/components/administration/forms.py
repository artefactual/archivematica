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
from django.forms import ModelForm
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput, Textarea, CheckboxInput
from main import models
from django.conf import settings
from components import helpers

class AdministrationForm(forms.Form):
    arguments = forms.CharField(required=False, widget=Textarea(attrs=settings.TEXTAREA_ATTRS))

class AgentForm(ModelForm):
    identifiervalue = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))
    name = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))

    class Meta:
        model = models.Agent
        exclude = ('identifiertype')

class ToggleSettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra_fields = kwargs.pop('extra', 0)
        super(ToggleSettingsForm, self).__init__(*args, **kwargs)

        for setting_name, setting_label in extra_fields.items():
            setting_value = helpers.get_setting(setting_name)
            if setting_value == 'False':
                setting_value = False
            else:
                setting_value = True
            self.fields[setting_name] = forms.BooleanField(
                label=setting_label,
                initial=setting_value,
                widget=CheckboxInput()
            )
