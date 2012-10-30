from django import forms
from django.forms import ModelForm
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput, Textarea
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
    ))

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
            'act': TextInput(attrs={'class': 'span11', 'title': "Act tooltip"}),
            'restriction': TextInput(attrs=INPUT_ATTRS),
            'startdate': TextInput(attrs={'class': 'span11', 'title': "Act start date tooltip"}),
            'enddate': TextInput(attrs={'class': 'span11', 'title': "Statute end date tooltip"}), }

class RightsGrantedNotesForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGrantedNote
        widgets = {
            'rightsgranted': TextInput(attrs=TEXTAREA_ATTRS), }

class RightsCopyrightForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyright
        widgets = {
            'copyrightstatus': TextInput(attrs={'class': 'span11', 'title': "Copyright status tooltip"}),
            'copyrightjurisdiction': TextInput(attrs={'class': 'span11', 'title': "Copyright jurisdiction tooltip"}),
            'copyrightstatusdeterminationdate': TextInput(attrs={'class': 'span11', 'title': "Copyright determination date tooltip"}),
            'copyrightapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "Copyright start date tooltip"}),
            'copyrightapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "Copyright end date tooltip"}), }

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
            'statutejurisdiction': TextInput(attrs={'class': 'span11', 'title': "Statute jurisdiction tooltip"}),
            'statutecitation': TextInput(attrs={'class': 'span11', 'title': "Statute action tooltip"}),
            'statutedeterminationdate': TextInput(attrs={'class': 'span11', 'title': "Statute determination date tooltip"}),
            'statuteapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "Statute start date tooltip"}),
            'statuteapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "Statute end date tooltip"}), }

class RightsStatuteNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementStatuteInformationNote
        widgets = {
            'statutenote': Textarea(attrs=TEXTAREA_ATTRS), }

class RightsOtherRightsForm(ModelForm):
    class Meta:
        model = models.RightsStatementOtherRightsInformation
        widgets = {
            'otherrightsbasis': TextInput(attrs={'class': 'span11', 'title': "Other rights basis"}),
            'otherrightsapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "Other rights start date tooltip"}),
            'otherrightsapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "Other rights end date tooltip"}), }

class RightsLicenseForm(ModelForm):
    class Meta:
        model = models.RightsStatementLicense
        widgets = {
            'licenseterms': TextInput(attrs={'class': 'span11', 'title': "License terms tooltip"}),
            'licenseapplicablestartdate': TextInput(attrs={'class': 'span11', 'title': "License start date tooltip"}),
            'licenseapplicableenddate': TextInput(attrs={'class': 'span11', 'title': "License end date tooltip"}), }

class RightsLicenseNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementLicenseNote
        widgets = {
            'licensenote': Textarea(attrs=TEXTAREA_ATTRS), }

class MicroServiceChoiceReplacementDicForm(ModelForm):
    class Meta:
        model = models.MicroServiceChoiceReplacementDic
        exclude = (
            'id',
            'choiceavailableatlink',)
        widgets = {
            'description': TextInput(attrs=INPUT_ATTRS),
            'replacementdic': Textarea(attrs=TEXTAREA_ATTRS), }
