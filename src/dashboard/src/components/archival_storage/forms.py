from django import forms


class CreateAICForm(forms.Form):
    results = forms.CharField(label=None, required=True, widget=forms.widgets.HiddenInput())

class ReingestAIPForm(forms.Form):
    METADATA_ONLY = 'metadata'
    OBJECTS = 'objects'
    REINGEST_CHOICES = (
        (METADATA_ONLY, 'Re-ingest metadata only'),
        (OBJECTS, 'Re-ingest metadata and objects')
    )
    reingest_type = forms.ChoiceField(choices=REINGEST_CHOICES,  widget=forms.RadioSelect, required=True)
