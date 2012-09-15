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
            'rightsnotes': Textarea(attrs=TEXTAREA_ATTRS),
            'rightsholder': TextInput(attrs=INPUT_ATTRS), }

class RightsGrantedForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGranted
        widgets = {
            'act': TextInput(attrs=INPUT_ATTRS),
            'restriction': TextInput(attrs=INPUT_ATTRS),
            'startdate': TextInput(attrs=INPUT_ATTRS),
            'enddate': TextInput(attrs=INPUT_ATTRS), }

class RightsGrantedNotesForm(ModelForm):
    class Meta:
        model = models.RightsStatementRightsGrantedNote
        widgets = {
            'rightsgranted': TextInput(attrs=TEXTAREA_ATTRS), }

class RightsCopyrightForm(ModelForm):
    class Meta:
        model = models.RightsStatementCopyright
        widgets = {
            'copyrightstatus': TextInput(attrs=INPUT_ATTRS),
            'copyrightjurisdiction': TextInput(attrs=INPUT_ATTRS),
            'copyrightstatusdeterminationdate': TextInput(attrs=INPUT_ATTRS),
            'copyrightapplicablestartdate': TextInput(attrs=INPUT_ATTRS),
            'copyrightapplicableenddate': TextInput(attrs=INPUT_ATTRS), }

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
            'statutejurisdiction': TextInput(attrs=INPUT_ATTRS),
            'statutecitation': TextInput(attrs=INPUT_ATTRS),
            'statutedeterminationdate': TextInput(attrs=INPUT_ATTRS),
            'statuteapplicablestartdate': TextInput(attrs=INPUT_ATTRS),
            'statuteapplicableenddate': TextInput(attrs=INPUT_ATTRS), }

class RightsStatuteNoteForm(ModelForm):
    class Meta:
        model = models.RightsStatementStatuteInformationNote
        widgets = {
            'statutenote': Textarea(attrs=TEXTAREA_ATTRS), }

class RightsOtherRightsForm(ModelForm):
    class Meta:
        model = models.RightsStatementOtherRightsInformation
        widgets = {
            'otherrightsbasis': TextInput(attrs=INPUT_ATTRS),
            'otherrightsapplicablestartdate': TextInput(attrs=INPUT_ATTRS),
            'otherrightsapplicableenddate': TextInput(attrs=INPUT_ATTRS), }

class RightsLicenseForm(ModelForm):
    class Meta:
        model = models.RightsStatementLicense
        widgets = {
            'licensetype': TextInput(attrs=INPUT_ATTRS),
            'licensevalue': TextInput(attrs=INPUT_ATTRS),
            'licenseterms': TextInput(attrs=INPUT_ATTRS),
            'licenseapplicablestartdate': TextInput(attrs=INPUT_ATTRS),
            'licenseapplicableenddate': TextInput(attrs=INPUT_ATTRS), }

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
