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

import sys
import traceback

from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.base import TemplateDoesNotExist

import elasticsearch


class AJAXSimpleExceptionResponseMiddleware:
    def process_exception(self, request, exception):
        if not settings.DEBUG or not request.is_ajax():
            return
        (exc_type, exc_info, tb) = sys.exc_info()
        response = "%s\n" % exc_type.__name__
        response += "%s\n\n" % exc_info
        response += "TRACEBACK:\n"
        for tb in traceback.format_tb(tb):
            response += "%s\n" % tb
        return HttpResponseServerError(response)


class SpecificExceptionErrorPageResponseMiddleware:
    def process_exception(self, request, exception):
        if settings.DEBUG and isinstance(exception, TemplateDoesNotExist):
            return HttpResponseServerError('Missing template: ' + str(exception))


class ElasticsearchMiddleware:
    """
    Redirect the user to a friendly error page when an exception related to
    Elasticsearch is detected.

    The goal is to inform the user that the error is related to Elasticsearch
    when they are running in production, as this seems to be a common problem,
    mainly because users frequently experience Elasticsearch node crashes when
    running them with not enough memory.
    """
    EXCEPTIONS = (
        elasticsearch.ElasticsearchException,
        elasticsearch.ImproperlyConfigured,
    )

    def process_exception(self, request, exception):
        if settings.DEBUG:
            return
        if isinstance(exception, self.EXCEPTIONS):
            return render(request, 'elasticsearch_error.html', {'exception_type': str(type(exception))})
