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

from django.conf import settings

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
    query = forms.CharField(label='', required=False, widget=TextInput(attrs=settings.INPUT_ATTRS))
      
class FPREditFormatID(forms.Form):
    formatID = forms.CharField(label = 'Format ID', required = True)
    purpose = forms.ChoiceField(choices = getPurposes())

    tool = forms.ChoiceField(choices = getTools())
    toolVersion = forms.CharField(label = 'Tool Version', required = False)

    formatDescription = forms.CharField(label = 'Description', required = False, max_length = 100,
        widget = TextInput(attrs = {'class':'Description'}))

    command = forms.CharField(label = 'Command', required = False, max_length = 100,
        widget = TextInput(attrs = {'class':'Description'}))

