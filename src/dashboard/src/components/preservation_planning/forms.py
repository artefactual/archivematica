
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon/externals")

from django.db import connection, transaction
from django.shortcuts import render
from django.http import HttpResponse
from main import models
from components import helpers

from django import forms
from django.forms.widgets import *

INPUT_ATTRS = {'class': 'span11'}

def getTools():
    query = 'SELECT description FROM FileIDTypes'

    cursor = connection.cursor()
    cursor.execute(query)

    ret = []
    for tool in cursor.fetchall():
        ret.append( (tool[0], tool[0]) )

    return ret

def getPurposes():
    query = 'SELECT classification FROM CommandClassifications'

    cursor = connection.cursor()
    cursor.execute(query)

    ret = []
    for purpose in cursor.fetchall():
        ret.append( (purpose[0], purpose[0]) )

    return ret

class FPRSearchForm(forms.Form):
    query = forms.CharField(label='', required=False, widget=TextInput(attrs=INPUT_ATTRS))

class FPREditFormatID(forms.Form):
    formatID = forms.CharField(label = 'Format ID', required = True)
    purpose = forms.ChoiceField(choices = getPurposes())

    tool = forms.ChoiceField(choices = getTools())
    toolVersion = forms.CharField(label = 'Tool Version', required = False)

    formatDescription = forms.CharField(label = 'Description', required = False, max_length = 100,
        widget = TextInput(attrs = {'class':'Description'}))

    command = forms.CharField(label = 'Command', required = False, max_length = 100,
        widget = TextInput(attrs = {'class':'Description'}))

