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

from re import compile as re_compile

from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

import components.helpers as helpers


EXEMPT_URLS = None


def _load_exempt_urls():
    global EXEMPT_URLS
    EXEMPT_URLS = [re_compile(settings.LOGIN_URL.lstrip("/"))]
    if hasattr(settings, "LOGIN_EXEMPT_URLS"):
        EXEMPT_URLS += [re_compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]


_load_exempt_urls()


class ConfigurationCheckMiddleware(MiddlewareMixin):
    """Redirect users to the installer page or the login page.

    The presence of the pipeline UUID in the database is an indicator of
    whether the application has already been set up.
    """

    def process_request(self, request):
        dashboard_uuid = helpers.get_setting("dashboard_uuid")

        # Start off the installer unless the user is already there.
        if not dashboard_uuid:
            if reverse("installer:welcome") == request.path_info:
                return
            return redirect("installer:welcome")

        # Send the user to the login page if needed.
        if not request.user.is_authenticated:
            path = request.path_info.lstrip("/")
            if not any(m.match(path) for m in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)

        # Share the ID of the pipeline with the application views.
        request.dashboard_uuid = dashboard_uuid
