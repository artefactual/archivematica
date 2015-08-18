# Standard library, alphabetical by import source
import logging

# Django Core, alphabetical by import source
from django.shortcuts import render

# External dependencies, alphabetical

# This project, alphabetical by import source
from components import decorators

logger = logging.getLogger('archivematica.dashboard')

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Appraisal
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """

@decorators.elasticsearch_required()
def appraisal(request):
    return render(request, 'appraisal/appraisal.html')
