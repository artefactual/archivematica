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
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy as _l


class SuperUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    org_name = forms.CharField(label=_l('Organization name'), help_text=_l('PREMIS agent name'), required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))
    org_identifier = forms.CharField(label=_l('Organization identifier'), help_text=_l('PREMIS agent identifier'), required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))

    class Meta:
        model = User
        fields = ['org_name', 'org_identifier', 'username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class OrganizationForm(forms.Form):
    """
    Simplified version of the superuser form - simply ask for organisation info
    """
    org_name = forms.CharField(label=_l('Organization name'), help_text=_l('PREMIS agent name'), required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))
    org_identifier = forms.CharField(label=_l('Organization identifier'), help_text=_l('PREMIS agent identifier'), required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))


class FPRConnectForm(forms.Form):
    comments = forms.CharField(required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))
