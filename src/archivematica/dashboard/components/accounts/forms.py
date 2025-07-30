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
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from archivematica.dashboard.main.models import UserProfile


class UserCreationForm(DjangoUserCreationForm):
    email = forms.EmailField(required=True)
    is_superuser = forms.BooleanField(label="Administrator", required=False)

    def save(self, commit=True):
        user = super().save(commit=False)
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
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password1")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)


class UserChangeForm(DjangoUserChangeForm):
    error_messages = {
        "password_mismatch": _(
            "The two password fields didn't match. Enter the same password as before, for verification."
        ),
        "current_password_required": _(
            "Your current password is required when setting a new password."
        ),
        "current_password_incorrect": _("Your current password is incorrect."),
    }
    email = forms.EmailField(required=True)
    current_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label=_("Your current password"),
        help_text=_("Required when setting a new password."),
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label=_("New password"),
        help_text=password_validators_help_text_html(),
    )
    password_confirmation = forms.CharField(
        widget=forms.PasswordInput, required=False, label="New password confirmation"
    )
    is_superuser = forms.BooleanField(label="Administrator", required=False)
    regenerate_api_key = forms.CharField(
        widget=forms.CheckboxInput,
        label="Regenerate API key?",
        required=False,
    )

    field_order = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_superuser",
        "current_password",
        "password",
        "password_confirmation",
        "regenerate_api_key",
    ]

    def __init__(self, *args, **kwargs):
        suppress_administrator_toggle = kwargs.pop(
            "suppress_administrator_toggle", False
        )
        try:
            self.requesting_user = kwargs.pop("requesting_user")
        except KeyError:
            raise ValueError("requesting_user is required for UserChangeForm")

        super().__init__(*args, **kwargs)

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

    def _validate_current_password(self, current_password):
        if not current_password:
            self.add_error(
                "current_password", self.error_messages["current_password_required"]
            )
            return False

        if not self.requesting_user.check_password(current_password):
            self.add_error(
                "current_password", self.error_messages["current_password_incorrect"]
            )
            return False

        return True

    def _validate_password_change(self, cleaned_data):
        """Validate password change requirements including current password verification."""
        password = cleaned_data.get("password", "")
        password_confirmation = cleaned_data.get("password_confirmation", "")
        current_password = cleaned_data.get("current_password", "")

        # Only validate if password change is being attempted.
        if not (password or password_confirmation):
            return

        if password != password_confirmation:
            self.add_error(
                "password_confirmation", self.error_messages["password_mismatch"]
            )

        self._validate_current_password(current_password)

    def clean(self):
        cleaned_data = super().clean()
        self._validate_password_change(cleaned_data)
        return cleaned_data

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class ApiKeyForm(forms.Form):
    regenerate_api_key = forms.BooleanField(
        widget=forms.CheckboxInput,
        label="Regenerate API key?",
        required=False,
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["system_emails"]
