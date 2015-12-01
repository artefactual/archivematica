from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms.widgets import TextInput, Textarea
from django.conf import settings

class SuperUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    org_name = forms.CharField(label='Organization name', help_text='PREMIS agent name', required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))
    org_identifier = forms.CharField(label='Organization identifier', help_text='PREMIS agent identifier', required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))

    class Meta:
        model = User
        fields = ['org_name', 'org_identifier', 'username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        if commit:
            user.save()
        return user

class FPRConnectForm(forms.Form):
    comments = forms.CharField(required=False, widget=TextInput(attrs=settings.INPUT_ATTRS)) 

