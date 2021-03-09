# -*- coding: utf-8 -*-
from __future__ import absolute_import
import atexit

import coverage
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

django.setup()
import elasticSearchFunctions

cov = coverage.Coverage(data_file="/src/cov/.coverage", data_suffix=True)
cov.start()


def save_coverage():
    cov.stop()
    cov.save()


atexit.register(save_coverage)

application = get_wsgi_application()

# Set up Elasticsearch client
elasticSearchFunctions.setup_reading_from_conf(settings)
