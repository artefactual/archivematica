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
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
    validate_password,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from main.models import UserProfile


class UserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_superuser = forms.BooleanField(label="Administrator", required=False)

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_superuser",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != "" and password2 != "":
            if password1 != password2:
                raise ValidationError(
                    self.error_messages["password_mismatch"], code="password_mismatch"
                )
        return password2

    def _post_clean(self):
        super(UserCreationForm, self)._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password1")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)


class UserChangeForm(UserChangeForm):
    error_messages = {
        "password_mismatch": _(
            "The two password fields didn’t match. Enter the same password as before, for verification."
        )
    }
    email = forms.EmailField(required=True)
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text=password_validators_help_text_html(),
    )
    password_confirmation = forms.CharField(widget=forms.PasswordInput, required=False)
    is_superuser = forms.BooleanField(label="Administrator", required=False)
    regenerate_api_key = forms.CharField(
        widget=forms.CheckboxInput,
        label="Regenerate API key (shown below)?",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        suppress_administrator_toggle = kwargs.get(
            "suppress_administrator_toggle", False
        )

        if "suppress_administrator_toggle" in kwargs:
            del kwargs["suppress_administrator_toggle"]

        super(UserChangeForm, self).__init__(*args, **kwargs)

        if suppress_administrator_toggle:
            del self.fields["is_superuser"]

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_superuser",
        )

    def clean_password(self):
        data = self.cleaned_data.get("password")
        return data

    def clean(self):
        cleaned_data = super(UserChangeForm, self).clean()
        if (
            cleaned_data.get("password") != ""
            or cleaned_data.get("password_confirmation") != ""
        ):
            if cleaned_data.get("password") != cleaned_data.get(
                "password_confirmation"
            ):
                self.add_error(
                    "password_confirmation", self.error_messages["password_mismatch"]
                )
        return cleaned_data

    def _post_clean(self):
        super(UserChangeForm, self)._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password", error)

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        if commit:
            user.save()
        return user


class ApiKeyForm(forms.Form):
    regenerate_api_key = forms.CharField(
        widget=forms.CheckboxInput,
        label="Regenerate API key (shown below)?",
        required=False,
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["system_emails"]
