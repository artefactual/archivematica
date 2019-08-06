# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import TextInput
from django.utils.translation import ugettext_lazy as _

from main.models import DashboardSetting


site_url_field = forms.CharField(
    label=_("Site URL"),
    help_text=_("This is the public URL of your Archivematica dashboard."),
    required=False,
    widget=TextInput(attrs=settings.INPUT_ATTRS),
)


class SuperUserCreationForm(UserCreationForm):
    site_url = site_url_field
    email = forms.EmailField(required=True)
    org_name = forms.CharField(
        label=_("Organization name"),
        help_text=_("PREMIS agent name"),
        required=False,
        widget=TextInput(attrs=settings.INPUT_ATTRS),
    )
    org_identifier = forms.CharField(
        label=_("Organization identifier"),
        help_text=_("PREMIS agent identifier"),
        required=False,
        widget=TextInput(attrs=settings.INPUT_ATTRS),
    )

    class Meta:
        model = User
        fields = [
            "org_name",
            "org_identifier",
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super(SuperUserCreationForm, self).__init__(*args, **kwargs)
        load_site_url(self.fields["site_url"])

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

    site_url = site_url_field
    org_name = forms.CharField(
        label=_("Organization name"),
        help_text=_("PREMIS agent name"),
        required=False,
        widget=TextInput(attrs=settings.INPUT_ATTRS),
    )
    org_identifier = forms.CharField(
        label=_("Organization identifier"),
        help_text=_("PREMIS agent identifier"),
        required=False,
        widget=TextInput(attrs=settings.INPUT_ATTRS),
    )

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        load_site_url(self.fields["site_url"])


def load_site_url(site_url_field):
    """Update form field with the application site URL."""
    if settings.SITE_URL:
        site_url_field.initial = settings.SITE_URL
        site_url_field.widget.attrs["readonly"] = True
        return
    try:
        setting = DashboardSetting.objects.get(name="site_url")
    except DashboardSetting.DoesNotExist:
        pass
    else:
        site_url_field.initial = setting.value
