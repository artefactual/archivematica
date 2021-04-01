# -*- coding: utf-8 -*-
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
from __future__ import absolute_import

import sys
import traceback
import logging

from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.utils.deprecation import MiddlewareMixin
from shibboleth.middleware import ShibbolethRemoteUserMiddleware

import elasticsearch


logger = logging.getLogger("archivematica.dashboard")


class AJAXSimpleExceptionResponseMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if not settings.DEBUG or not request.is_ajax():
            return
        (exc_type, exc_info, tb) = sys.exc_info()
        tracebacks = traceback.format_tb(tb)
        logger.error(
            "Processing exception %s at %s. Traceback %s",
            exception,
            request.path,
            tracebacks,
        )
        response = "%s\n" % exc_type.__name__
        response += "%s\n\n" % exc_info
        response += "TRACEBACK:\n"
        for tb in tracebacks:
            response += "%s\n" % tb
        return HttpResponseServerError(response)


class SpecificExceptionErrorPageResponseMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if settings.DEBUG and isinstance(exception, TemplateDoesNotExist):
            return HttpResponseServerError("Missing template: " + str(exception))


class ElasticsearchMiddleware(MiddlewareMixin):
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
            return render(
                request,
                "elasticsearch_error.html",
                {"exception_type": str(type(exception))},
            )


class AuditLogMiddleware(object):
    """Add X-Username header with authenticated user to responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["X-Username"] = request.user.get_username()
        return response


SHIBBOLETH_REMOTE_USER_HEADER = getattr(
    settings, "SHIBBOLETH_REMOTE_USER_HEADER", "REMOTE_USER"
)


class CustomShibbolethRemoteUserMiddleware(ShibbolethRemoteUserMiddleware):
    """
    Custom version of Shibboleth remote user middleware

    THe aim of this is to provide a custom header name that is expected
    to identify the remote Shibboleth user
    """

    header = SHIBBOLETH_REMOTE_USER_HEADER

    def make_profile(self, user, shib_meta):
        """
        Customize the user based on shib_meta mappings (anything that's not
        already covered by the attribute map)
        """
        # Make the user an administrator if they are in the designated admin group
        entitlements = shib_meta["entitlement"].split(";")
        user.is_superuser = settings.SHIBBOLETH_ADMIN_ENTITLEMENT in entitlements
        user.save()
