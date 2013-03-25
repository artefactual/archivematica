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
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm

class UserCreationForm(UserCreationForm):
    def clean_password1(self):
        data = self.cleaned_data['password1']
        if data != '' and len(data) < 8:
            raise forms.ValidationError('Password should be at least 8 characters long')
        return data

class UserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirmation = forms.CharField(widget=forms.PasswordInput, required=False)
    regenerate_api_key = forms.CharField(widget=forms.CheckboxInput, label='Regenerate API key (shown below)?')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        ## Hide fields when there is only one superuser
        if 1 == User.objects.filter(is_superuser=True).count():
            del self.fields['is_active']
            del self.fields['is_superuser']

    def clean_password(self):
        data = self.cleaned_data['password']
        if self.cleaned_data['password'] != '' and len(self.cleaned_data['password']) < 8:
            raise forms.ValidationError('Password should be at least 8 characters long')
        return data

    def clean(self):
        cleaned_data = super(UserChangeForm, self).clean()
        if cleaned_data.get('password') != '' or cleaned_data.get('password_confirmation') != '':
            if cleaned_data.get('password') != cleaned_data.get('password_confirmation'):
                raise forms.ValidationError('Password and password confirmation do not match')
        return cleaned_data

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        if commit:
            user.save()
        return user
