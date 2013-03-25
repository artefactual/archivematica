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
from django.forms.widgets import TextInput, Textarea, CheckboxInput, HiddenInput
from main import models
from django.conf import settings

class RightsForm(ModelForm):
    rightsbasis = forms.ChoiceField(label="Basis", choices=(
        ('Copyright', 'Copyright'),
        ('Statute', 'Statute'),
        ('License', 'License'),
        ('Donor', 'Donor'),
        ('Policy', 'Policy'),
        ('Other', 'Other')
    ), widget=forms.Select(attrs={'title': "designation of the basis for the right or permission described in the rightsStatementIdentifier"}))

    class Meta:
        model = models.RightsStatement
        exclude = (
            'id',
            'metadataappliestotype',
            'metadataappliestoidentifier',
            'rightsstatementidentifiertype',
            'rightsstatementidentifiervalue',
            'rightsholder',)
        widgets = {
            'rightsholder': TextInput(attrs=settings.INPUT_ATTRS), }

class RightsGrantedForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGranted
        widgets = {
            'act': TextInput(attrs={'class': 'span11', 'title': "the action the preservation repository is allowed to take; eg replicate, migrate, modify, use, disseminate, delete"}),
            'restriction': TextInput(attrs=settings.INPUT_ATTRS),
            'startdate': TextInput(attrs={'class': 'span11', 'title': "beginning date of the rights or restrictions granted"}),
            'enddate': TextInput(attrs={'class': 'span11', 'title': "ending date of the rights or restrictions granted"}),
            'enddateopen': CheckboxInput(attrs={'title': 'use "OPEN" for an open ended term of restriction. Omit endDate if the ending date is unknown or the permission statement applies to many objects with different end dates.'}), }

class RightsGrantedNotesForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGrantedNote
        widgets = {
            'rightsgranted': TextInput(attrs=settings.TEXTAREA_ATTRS), }

class RightsCopyrightForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyright
        widgets = {
            'copyrightstatus': TextInput(attrs={'class': 'span11', 'title': "a coded designation of the copyright status of the object at the time the rights statement is recorded; eg copyrighted, publicdomain, unknown"}),
            'copyrightjurisdiction': TextInput(attrs={'class': 'span11', 'title': "the country whose copyright laws apply [ISO 3166]"}),
            'copyrightstatusdeterminationdate': TextInput(attrs={'class': 'span11', 'title': "the date that the copyright status recorded in copyrightStatus was determined"}),
            'copyrightapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "date when the particular copyright applies or is applied to the content"}),
            'copyrightapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "date when the particular copyright no longer applies or is applied to the content"}), }

class RightsStatementCopyrightDocumentationIdentifierForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyrightDocumentationIdentifier
        widgets = {
          'copyrightdocumentationidentifiertype': TextInput(attrs=settings.INPUT_ATTRS),
          'copyrightdocumentationidentifiervalue': TextInput(attrs=settings.INPUT_ATTRS),
          'copyrightdocumentationidentifierrole': TextInput(attrs=settings.INPUT_ATTRS), }

class RightsCopyrightNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyrightNote
        widgets = {
            'copyrightnote': Textarea(attrs=settings.TEXTAREA_ATTRS), }

class RightsStatuteForm(ModelForm):
    class Meta:
        model = models.RightsStatementStatuteInformation
        widgets = {
            'statutejurisdiction': TextInput(attrs={'class': 'span11', 'title': "the country or other political body enacting the statute"}),
            'statutecitation': TextInput(attrs={'class': 'span11', 'title': "an identifying designation for the statute"}),
            'statutedeterminationdate': TextInput(attrs={'class': 'span11', 'title': "date that the determination was made that the statue authorized the permission(s) noted"}),
            'statuteapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "the date when the statute begins to apply or is applied to the content"}),
            'statuteapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "the date when the statute ceasees to apply or be applied to the content"}), }

class RightsStatuteNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementStatuteInformationNote
        widgets = {
            'statutenote': Textarea(attrs=settings.TEXTAREA_ATTRS), }

class RightsOtherRightsForm(ModelForm):
    class Meta:
        model = models.RightsStatementOtherRightsInformation
        widgets = {
            'otherrightsbasis': TextInput(attrs={'class': 'span11', 'title': "designation of the basis for the other right or permission described in the rightsStatementIdentifier"}),
            'otherrightsapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "date when the other right applies or is applied to the content"}),
            'otherrightsapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "date when the other right no longer applies or is applied to the content"}), }

class RightsLicenseForm(ModelForm):
    class Meta:
        model = models.RightsStatementLicense
        widgets = {
            'licenseterms': TextInput(attrs={'class': 'span11', 'title': "Text describing the license or agreement by which permission as granted"}),
            'licenseapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "the date at which the license first applies or is applied to the content"}),
            'licenseapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "the end date at which the license no longer applies or is applied to the content"}), }

class RightsLicenseNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementLicenseNote
        widgets = {
            'licensenote': Textarea(attrs=settings.TEXTAREA_ATTRS), }
