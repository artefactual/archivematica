from django import forms
from main import models
from django.conf import settings


class MicroServiceChoiceReplacementDicForm(forms.ModelForm):
    class Meta:
        model = models.MicroServiceChoiceReplacementDic
        fields = ('choiceavailableatlink', 'description', 'replacementdic')
        widgets = {
            'description': forms.widgets.TextInput(attrs=settings.INPUT_ATTRS),
            'replacementdic': forms.widgets.Textarea(attrs=settings.TEXTAREA_ATTRS),
            'choiceavailableatlink': forms.widgets.HiddenInput
        }


class EventDetailForm(forms.ModelForm):
    class Meta:
        model = models.Event
        fields = ('event_detail',)
        widgets = {
            'event_detail': forms.widgets.Textarea(attrs=settings.TEXTAREA_ATTRS),
        }
