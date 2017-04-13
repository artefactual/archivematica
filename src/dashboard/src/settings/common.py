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

import os
import ConfigParser

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

path_of_this_file = os.path.abspath(os.path.dirname(__file__))

BASE_PATH = os.path.abspath(os.path.join(path_of_this_file, os.pardir))


def get_env_variable(var_name):
    """ Get the environment variable or return exception """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)


# Django settings for app project.

DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Get DB settings from main configuration file
config = ConfigParser.SafeConfigParser()
config.read('/etc/archivematica/archivematicaCommon/dbsettings')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',         # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': config.get('client', 'database'),     # Or path to database file if using sqlite3.
        'USER': config.get('client', 'user'),         # Not used with sqlite3.
        'PASSWORD': config.get('client', 'password'), # Not used with sqlite3.
        'HOST': config.get('client', 'host'),         # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                                   # Set to empty string for default. Not used with sqlite3.
    }
}

# Memcached is the most efficient cache backend natively supported by Django.
# However, Memcached is not available yet in the Archivetica stack but we may
# consider adding it soon. Using local-memory caching for now so we can start
# writing some cache-aware code.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# https://docs.djangoproject.com/en/dev/ref/settings/#languages
LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
    ('es', _('Spanish')),
]

LOCALE_PATHS = [
    os.path.join(BASE_PATH, 'locale'),
]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Enable timezone support, for more info see:
# https://docs.djangoproject.com/en/dev/topics/i18n/timezones/
USE_TZ = True

# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TIME_ZONE
TIME_ZONE = 'UTC'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_PATH, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/media/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/media/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ('js', os.path.join(BASE_PATH, 'media', 'js')),
    ('css', os.path.join(BASE_PATH, 'media', 'css')),
    ('images', os.path.join(BASE_PATH, 'media', 'images')),
    ('vendor', os.path.join(BASE_PATH, 'media', 'vendor')),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_PATH, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

MIDDLEWARE_CLASSES = (
    # 'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'middleware.common.AJAXSimpleExceptionResponseMiddleware',
    'installer.middleware.ConfigurationCheckMiddleware',
    'middleware.common.SpecificExceptionErrorPageResponseMiddleware',
    'middleware.common.ElasticsearchMiddleware',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    # Django basics
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.webdesign',

    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',

    # Internal apps
    'installer',
    'components.accounts',
    'main',
    'components.mcp',
    'components.administration',

    # FPR
    'fpr',

    # For REST API
    'tastypie',

    'django_forms_bootstrap',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# For configuration option details see:
# https://docs.djangoproject.com/en/1.8/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '127.0.0.1'
EMAIL_TIMEOUT = 15

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)-8s  %(name)s.%(funcName)s:  %(message)s',
        },
        'detailed': {
            'format': '%(levelname)-8s  %(asctime)s  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'archivematica.mcp': {
            'propagate': False,
        },
        'archivematica': {
            'level': 'DEBUG',
        },
        'elasticsearch': {
            'level': 'INFO',
        },
        'agentarchives': {
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# login-related settings
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/administration/accounts/login/'
LOGIN_EXEMPT_URLS  = [
  r'^administration/accounts/login',
  r'^api'
]

# Django debug toolbar
try:
    import debug_toolbar
except:
    pass
else:
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
    INTERNAL_IPS = ('127.0.0.1', '192.168.82.1', '10.0.2.2')
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }

# Dashboard internal settings
GEARMAN_SERVER = os.environ.get('ARCHIVEMATICA_DASHBOARD_GEARMAN', 'localhost:4730')
POLLING_INTERVAL = 5 # Seconds
STATUS_POLLING_INTERVAL = 5 # Seconds
TASKS_PER_PAGE = 10 # for paging in tasks dialog
UUID_REGEX = '[\w]{8}(-[\w]{4}){3}-[\w]{12}'

FPR_URL = 'https://fpr.archivematica.org/fpr/api/v2/'
FPR_VERIFY_CERT = True

ALLOWED_HOSTS = get_env_variable('DJANGO_ALLOWED_HOSTS').split(',')

MICROSERVICES_HELP = {
    'Approve transfer': _('Select "Approve transfer" to begin processing or "Reject transfer" to start over again.'),
    'Workflow decision - create transfer backup': _('Create a complete backup of the transfer in case transfer/ingest are interrupted or fail. The transfer will automatically be deleted once the AIP has been moved into storage.'),
    'Workflow decision - send transfer to quarantine': _('If desired, quarantine transfer to allow definitions in anti-virus software to be updated.'),
    'Remove from quarantine': _('If desired, select "Unquarantine" to remove the transfer from quarantine immediately. Otherwise, wait until the quarantine period has expired and the transfer will be removed automatically.'),
    'Create SIP(s)': _('Create a SIP from the transfer.'),
    'Approve SIP Creation': _('Once you have added files from the transfer to the SIP and have completed any appraisal and physical arrangement, select "SIP creation complete" to start ingest micro-services.'),
    'Normalize': _('Create preservation and/or access copies of files if desired. Creating access copies will result in a DIP being generated for upload into an access system.'),
    'Approve normalization': _('If desired, click "review" to view the normalized files. To see a report summarizing the normalization results, click on the report icon next to the Actions drop-down menu. If normalization has failed, click on "Yes" under "Preservation normalization failed" or "Access normalization failed" to view the tool output and error message.'),
    'Store AIP': _('If desired, click "review" to view AIP contents. Select "Store AIP" to move the AIP into archival storage.'),
    'UploadDIP': _('If desired, select "Upload DIP" to upload the DIP to the access system.'),
}

# Form styling
TEXTAREA_ATTRS           = {'rows': '4', 'class': 'span11'}
TEXTAREA_WITH_HELP_ATTRS = {'rows': '4', 'class': 'span11 has_contextual_help'}
INPUT_ATTRS              = {'class': 'span11'}
INPUT_WITH_HELP_ATTRS    = {'class': 'span11 has_contextual_help'}
