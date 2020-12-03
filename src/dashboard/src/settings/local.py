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

"""Development settings and globals."""
from __future__ import absolute_import

import os

from .base import *


DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

# Disable password validation in local development environment.
AUTH_PASSWORD_VALIDATORS = []

# Fixture directories are only configured in local and test environments.
# In Django 1.8, if you create a fixture named initial_data.[xml/yaml/json],
# that fixture will be loaded every time you run migrate, which is something we
# want to avoid in production environments.
FIXTURE_DIRS = (
    os.path.abspath(os.path.join(BASE_PATH, os.pardir, "tests", "fixtures")),
)
