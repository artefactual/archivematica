# -*- coding: utf-8 -*-

# flake8: noqa

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

"""Test settings and globals."""
from __future__ import absolute_import

import ldap
from django_auth_ldap.config import LDAPSearch

# Import local settings (base settings + debug + fixture dirs)
from .local import *


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "archivematica-test.db",
        "TEST": {"NAME": "archivematica-test.db"},
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)-8s  %(name)s.%(funcName)s:  %(message)s"}
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}

# Disable whitenoise
STATICFILES_STORAGE = None
if MIDDLEWARE[0] == "whitenoise.middleware.WhiteNoiseMiddleware":
    del MIDDLEWARE[0]


# Special testing setup for LDAP tests in test_ldap.py
# (since override_settings would take effect too late)
AUTH_LDAP_SERVER_URI = "ldap://localhost/"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=example,o=test", ldap.SCOPE_SUBTREE, "(cn=%(user)s)"
)
AUTH_LDAP_USER_FLAGS_BY_GROUP = {}
AUTH_LDAP_USERNAME_SUFFIX = "_ldap"
