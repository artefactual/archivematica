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
from components import helpers
from django.forms import ModelForm
from django.forms.widgets import TextInput, Textarea, RadioSelect, CheckboxInput
from main import models
from django.conf import settings
from components.administration.models import ArchivistsToolkitConfig

class AtomSettingsForm(forms.ModelForm):
    class Meta:
        model = models.StandardTaskConfig
        fields = ('arguments',)

    def __init__(self, *args, **kwargs):
        super(AtomSettingsForm, self).__init__(*args, **kwargs)
        # Should add this to Meta: widgets but unsure how to modify 'class' in place
        arguments_attrs = settings.TEXTAREA_ATTRS
        arguments_attrs['class'] += ' command'
        self.fields['arguments'].widget.attrs = arguments_attrs
        # TODO in Django 1.6 move this to Meta: help_texts
        self.fields['arguments'].help_text = "Note that a backslash is necessary for each new line."

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

EAD_SHOW_CHOICES = [['embed', 'embed'], ['new','new'], ['none','none'], ['other','other'], ['replace', 'replace']]
EAD_ACTUATE_CHOICES = [['none', 'none'], ['onLoad','onLoad'],['other','other'], ['onRequest', 'onRequest']]
PREMIS_CHOICES = [[ 'yes', 'yes'], ['no', 'no'], ['premis', 'base on PREMIS']]

class ArchivistsToolkitConfigForm(ModelForm):
    id = forms.HiddenInput()
    host = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="db host:")
    port = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="db port:")
    dbname = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="db name:")
    dbuser = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="db user:")
    dbpass = forms.CharField(widget=forms.PasswordInput(), label="db password:", required=False)
    atuser = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="at username:")
    premis = forms.ChoiceField(widget=RadioSelect(), label="Restrictions Apply:", choices=PREMIS_CHOICES)
    ead_actuate = forms.ChoiceField(widget=RadioSelect(), label="EAD DAO Actuate:", choices=EAD_ACTUATE_CHOICES)
    ead_show = forms.ChoiceField(widget=RadioSelect(), label="EAD DAO Show:", choices=EAD_SHOW_CHOICES)
    use_statement = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="Use statement:")
    object_type = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="Object type:", required=False)
    access_conditions = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="Conditions governing access:", required=False)
    use_conditions = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="Conditions governing use:", required=False)
    uri_prefix = forms.CharField(widget=TextInput(attrs=settings.INPUT_ATTRS), label="URL prefix:")    
 
    class Meta:
        model = ArchivistsToolkitConfig

class TaxonomyTermForm(ModelForm):
    taxonomyuuid = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))
    term = forms.CharField(required=True, widget=TextInput(attrs=settings.INPUT_ATTRS))

    class Meta:
        model = models.TaxonomyTerm
        exclude = ('identifiertype')
