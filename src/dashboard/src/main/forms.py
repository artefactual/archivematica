from django import forms
from django.forms import ModelForm
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput, Textarea, CheckboxInput, HiddenInput
from main import models

TEXTAREA_ATTRS = {'rows': '4', 'class': 'span11'}
INPUT_ATTRS = {'class': 'span11'}

class DublinCoreMetadataForm(forms.Form):
    title = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    creator = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    subject = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    description = forms.CharField(required=False, widget=Textarea(attrs=TEXTAREA_ATTRS))
    publisher = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    contributor = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    date = forms.CharField(required=False, help_text='Use ISO 8061 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)', widget=TextInput(attrs=INPUT_ATTRS))
    type = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    format = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    identifier = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    source = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    relation = forms.CharField(required=False, label='Relation', widget=TextInput(attrs=INPUT_ATTRS))
    language = forms.CharField(required=False, help_text='Use ISO 3166', widget=TextInput(attrs=INPUT_ATTRS))
    coverage = forms.CharField(required=False, widget=TextInput(attrs=INPUT_ATTRS))
    rights = forms.CharField(required=False, widget=Textarea(attrs=TEXTAREA_ATTRS))

class AdministrationForm(forms.Form):
    arguments = forms.CharField(required=False, widget=Textarea(attrs=TEXTAREA_ATTRS))

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
            'rightsholder': TextInput(attrs=INPUT_ATTRS), }

class RightsGrantedForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGranted
        widgets = {
            'act': TextInput(attrs={'class': 'span11', 'title': "the action the preservation repository is allowed to take; eg replicate, migrate, modify, use, disseminate, delete"}),
            'restriction': TextInput(attrs=INPUT_ATTRS),
            'startdate': TextInput(attrs={'class': 'span11', 'title': "beginning date of the rights or restrictions granted"}),
            'enddate': TextInput(attrs={'class': 'span11', 'title': "ending date of the rights or restrictions granted"}),
            'enddateopen': CheckboxInput(attrs={'title': 'use "OPEN" for an open ended term of restriction. Omit endDate if the ending date is unknown or the permission statement applies to many objects with different end dates.'}), }

class RightsGrantedNotesForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGrantedNote
        widgets = {
            'rightsgranted': TextInput(attrs=TEXTAREA_ATTRS), }

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
          'copyrightdocumentationidentifiertype': TextInput(attrs=INPUT_ATTRS),
          'copyrightdocumentationidentifiervalue': TextInput(attrs=INPUT_ATTRS),
          'copyrightdocumentationidentifierrole': TextInput(attrs=INPUT_ATTRS), }

class RightsCopyrightNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyrightNote
        widgets = {
            'copyrightnote': Textarea(attrs=TEXTAREA_ATTRS), }

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
            'statutenote': Textarea(attrs=TEXTAREA_ATTRS), }

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
            'licensenote': Textarea(attrs=TEXTAREA_ATTRS), }

class MicroServiceChoiceReplacementDicForm(ModelForm):
    class Meta:
        model = models.MicroServiceChoiceReplacementDic
        exclude = (
            'id', )
        widgets = {
            'description': TextInput(attrs=INPUT_ATTRS),
            'replacementdic': Textarea(attrs=TEXTAREA_ATTRS),
            'choiceavailableatlink': HiddenInput
        }
