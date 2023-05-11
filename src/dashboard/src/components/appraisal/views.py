import logging

from django.shortcuts import render

logger = logging.getLogger("archivematica.dashboard")

""" @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      Appraisal
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ """


def appraisal(request):
    return render(request, "appraisal/appraisal.html")
