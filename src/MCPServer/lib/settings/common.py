# This file is part of Archivematica.
#
# Copyright 2010-2015 Artefactual Systems Inc. <http://artefactual.com>
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

import os, sys, ConfigParser

# Get DB settings from main configuration file
config = ConfigParser.SafeConfigParser()
config.read('/etc/archivematica/archivematicaCommon/dbsettings')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config.get('client', 'database'),          # Or path to database file if using sqlite3.
        'USER': config.get('client', 'user'),              # Not used with sqlite3.
        'PASSWORD': config.get('client', 'password'),      # Not used with sqlite3.
        'HOST': config.get('client', 'host'),              # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                                        # Set to empty string for default. Not used with sqlite3.
        'CONN_MAX_AGE': 500,
    }
}

MYSQLPOOL_BACKEND = 'QueuePool'
MYSQLPOOL_ARGUMENTS = {
    'use_threadlocal': False,
}

CONN_MAX_AGE = 14400

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48'

USE_TZ = True
TIME_ZONE = 'UTC'
