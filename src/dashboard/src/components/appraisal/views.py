# Standard library, alphabetical by import source
from __future__ import absolute_import
import logging

# Django Core, alphabetical by import source
from django.shortcuts import render

# External dependencies, alphabetical

# This project, alphabetical by import source

logger = logging.getLogger("archivematica.dashboard")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Appraisal
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def appraisal(request):
    return render(request, "appraisal/appraisal.html")
