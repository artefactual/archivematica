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
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

import components.helpers as helpers
from re import compile as re_compile


EXEMPT_URLS = [re_compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [re_compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]


class ConfigurationCheckMiddleware:
    def process_request(self, request):
        # The presence of the UUID is an indicator of whether we've already set up.
        dashboard_uuid = helpers.get_setting('dashboard_uuid')
        if not dashboard_uuid:
            # Start off the installer
            if reverse('installer.views.welcome') != request.path_info:
                return redirect('installer.views.welcome')
        elif not request.user.is_authenticated():
            # Installation already happened - make sure the user is logged in.
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)
