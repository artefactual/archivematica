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


class CreateAICForm(forms.Form):
    results = forms.CharField(label=None, required=True, widget=forms.widgets.HiddenInput())


class ReingestAIPForm(forms.Form):
    METADATA_ONLY = 'metadata'
    OBJECTS = 'objects'
    FULL = 'full'
    REINGEST_CHOICES = (
        (METADATA_ONLY, 'Metadata re-ingest'),
        (OBJECTS, 'Partial re-ingest'),
        (FULL, 'Full re-ingest'),
    )
    reingest_type = forms.ChoiceField(choices=REINGEST_CHOICES,  widget=forms.RadioSelect, required=True)
    processing_config = forms.CharField(required=False, initial='default',
        help_text='Only needed in full re-ingest',
        widget=forms.TextInput(attrs={'placeholder': 'default'}))
