from django import forms
from main import models
from django.conf import settings

class DublinCoreMetadataForm(forms.ModelForm):
    class Meta:
        model = models.DublinCore
        fields = ('title', 'is_part_of', 'creator', 'subject', 'description', 'publisher', 'contributor', 'date', 'format', 'identifier', 'source', 'relation', 'language', 'coverage', 'rights')
        widgets = {
            'title': forms.TextInput,
            'is_part_of': forms.TextInput,
            'creator': forms.TextInput,
            'subject': forms.TextInput,
            'publisher': forms.TextInput,
            'contributor': forms.TextInput,
            'date': forms.TextInput,
            'type': forms.TextInput,
            'format': forms.TextInput,
            'identifier': forms.TextInput,
            'source': forms.TextInput,
            'relation': forms.TextInput,
            'language': forms.TextInput,
            'coverage': forms.TextInput,
        }

    aic_prefix = 'AIC#'

    def __init__(self, *args, **kwargs):
        super(DublinCoreMetadataForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.widgets.TextInput):
                self.fields[field].widget.attrs = settings.INPUT_WITH_HELP_ATTRS
            elif isinstance(self.fields[field].widget, forms.widgets.Textarea):
                self.fields[field].widget.attrs = settings.TEXTAREA_WITH_HELP_ATTRS

    def save(self, *args, **kwargs):
        # Status is set to REINGEST when metadata is parsed into the DB. If it
        # is being saved through this form, then the user has modified it, and
        # it should not be written out to the METS file. Set the status to
        # UPDATED to indicate this.
        if self.instance.status == models.METADATA_STATUS_REINGEST:
            self.instance.status = models.METADATA_STATUS_UPDATED
        return super(DublinCoreMetadataForm, self).save(*args, **kwargs)

    def clean_is_part_of(self):
        data = self.cleaned_data['is_part_of']
        if data and not data.startswith(self.aic_prefix):
            data = self.aic_prefix+data
        return data

class AICDublinCoreMetadataForm(DublinCoreMetadataForm):
    class Meta:
        model = models.DublinCore
        fields = ('title', 'identifier', 'creator', 'subject', 'description', 'publisher', 'contributor', 'date', 'format', 'source', 'relation', 'language', 'coverage', 'rights')  # Removed 'is_part_of'
        widgets = DublinCoreMetadataForm.Meta.widgets.copy()

    def __init__(self, *args, **kwargs):
        super(AICDublinCoreMetadataForm, self).__init__(*args, **kwargs)
        self.fields['identifier'].required = True

    def clean_identifier(self):
        data = self.cleaned_data['identifier']
        if data and not data.startswith(self.aic_prefix):
            data = self.aic_prefix+data
        return data

