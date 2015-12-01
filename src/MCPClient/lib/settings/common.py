import os, sys, ConfigParser
import django_mysqlpool

# Get DB settings from main configuration file
config = ConfigParser.SafeConfigParser()
config.read('/etc/archivematica/archivematicaCommon/dbsettings')

DATABASES = {
    'default': {
        'ENGINE': 'django_mysqlpool.backends.mysqlpool',
        'NAME': 'MCP',                                     # Or path to database file if using sqlite3.
        'USER': config.get('client', 'user'),              # Not used with sqlite3.
        'PASSWORD': config.get('client', 'password'),      # Not used with sqlite3.
        'HOST': config.get('client', 'host'),              # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                                        # Set to empty string for default. Not used with sqlite3.
    }
}

MYSQLPOOL_BACKEND = 'QueuePool'
MYSQLPOOL_ARGUMENTS = {
    'use_threadlocal': False,
}

CONN_MAX_AGE = 14400

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48'
