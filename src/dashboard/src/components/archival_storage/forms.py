from django import forms
from django.forms.widgets import TextInput, Textarea

INPUT_ATTRS = {'class': 'span11'}

class StorageSearchForm(forms.Form):
    query = forms.CharField(label='', required=False, widget=TextInput(attrs=INPUT_ATTRS))
