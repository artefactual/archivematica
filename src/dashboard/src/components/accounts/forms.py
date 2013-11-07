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
    is_superuser = forms.BooleanField(label = 'Administrator',required=False)

    def clean_password1(self):
        data = self.cleaned_data['password1']
        if data != '' and len(data) < 8:
            raise forms.ValidationError('Password should be at least 8 characters long')
        return data
    
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        if commit:
            user.save()
        return user


    class Meta:
        model = User
        fields = ('username', 'first_name','last_name','email', 'is_active','is_superuser')

class UserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirmation = forms.CharField(widget=forms.PasswordInput, required=False)
    is_superuser = forms.BooleanField(label = 'Administrator', required=False)
    regenerate_api_key = forms.CharField(widget=forms.CheckboxInput, label='Regenerate API key (shown below)?')

    def __init__(self, *args, **kwargs):
        suppress_administrator_toggle = kwargs.get('suppress_administrator_toggle', False)

        if 'suppress_administrator_toggle' in kwargs:
            del kwargs['suppress_administrator_toggle']

        super(UserChangeForm, self).__init__(*args, **kwargs)

        if suppress_administrator_toggle:
            del self.fields['is_superuser']

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser')
            
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
