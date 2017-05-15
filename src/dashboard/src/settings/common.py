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

import ConfigParser
import StringIO
import os

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from env_configparser import EnvConfigParser


class Config(object):
    ENV_PREFIX = 'ARCHIVEMATICA_DASHBOARD'

    DBSETTINGS_FILE = '/etc/archivematica/archivematicaCommon/dbsettings'
    DBSETTINGS_CONFIG = """[client]
user = archivematica
password = demo
host = localhost
database = MCP
max_overflow = 40
port = 3306
engine = django_mysqlpool.backends.mysqlpool
    """

    """
    Mapping configuration attributes with INI section, options and types.
    """
    MAPPING = {
        'secret_key': {'section': 'Dashboard', 'option': 'django_secret_key', 'type': 'string'},
        'shared_directory': {'section': 'Dashboard', 'option': 'shared_directory', 'type': 'string'},
        'watch_directory': {'section': 'Dashboard', 'option': 'watch_directory', 'type': 'string'},
        'elasticsearch_server': {'section': 'Dashboard', 'option': 'elasticsearch_server', 'type': 'string'},

        # [client]
        'db_engine': {'section': 'client', 'option': 'engine', 'type': 'string'},
        'db_name': {'section': 'client', 'option': 'database', 'type': 'string'},
        'db_user': {'section': 'client', 'option': 'user', 'type': 'string'},
        'db_password': {'section': 'client', 'option': 'password', 'type': 'string'},
        'db_host': {'section': 'client', 'option': 'host', 'type': 'string'},
        'db_port': {'section': 'client', 'option': 'port', 'type': 'string'},
        'db_pool_max_overflow': {'section': 'client', 'option': 'max_overflow', 'type': 'string'},
    }

    def __init__(self):
        self.config = EnvConfigParser(prefix=self.ENV_PREFIX)

        self.read_defaults()
        self.read_files()

    def read_defaults(self):
        self.config.readfp(StringIO.StringIO(self.DBSETTINGS_CONFIG))

    def read_files(self):
        self.config.read([self.DBSETTINGS_FILE])

    def get(self, attr, default=None):
        if attr not in self.MAPPING:
            raise ImproperlyConfigured('Unknown attribute: %s. Make sure the attribute is included in the MAPPING property in `common.py`.' % attr)

        attr_opts = self.MAPPING[attr]
        if not all(k in attr_opts for k in ('section', 'option', 'type')):
            raise ImproperlyConfigured('Invalid attribute: %s. Make sure the entry in MAPPING in common.py has all the fields needed (section, option, type).' % attr)

        getter = 'get{}'.format('' if attr_opts['type'] == 'string' else attr_opts['type'])
        kwargs = {'section': attr_opts['section'], 'option': attr_opts['option']}
        if default is not None:
            kwargs['fallback'] = default
        elif 'default' in attr_opts:
            kwargs['fallback'] = attr['default']

        try:
            return getattr(self.config, getter)(**kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise ImproperlyConfigured('The following configuration attribute must be defined: %s.' % attr)


config = Config()

path_of_this_file = os.path.abspath(os.path.dirname(__file__))

BASE_PATH = os.path.abspath(os.path.join(path_of_this_file, os.pardir))

# Django settings for app project.

DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': config.get('db_engine'),
        'NAME': config.get('db_name'),
        'USER': config.get('db_user'),
        'PASSWORD': config.get('db_password'),
        'HOST': config.get('db_host'),
        'PORT': config.get('db_port'),
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

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('secret_key', default='e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_PATH, 'templates'), ],
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
        'logfile': {
            'level': 'INFO',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/dashboard/dashboard.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 20 * 1024 * 1024,  # 20 MiB
        },
        'verboselogfile': {
            'level': 'DEBUG',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/dashboard/dashboard.debug.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 100 * 1024 * 1024,  # 100 MiB
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
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
LOGIN_EXEMPT_URLS = [
    r'^administration/accounts/login',
    r'^api'
]

# Django debug toolbar
try:
    import debug_toolbar  # noqa: F401
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
MCP_SERVER = ('127.0.0.1', 4730)  # localhost:4730
POLLING_INTERVAL = 5  # Seconds
STATUS_POLLING_INTERVAL = 5  # Seconds
TASKS_PER_PAGE = 10  # for paging in tasks dialog
UUID_REGEX = '[\w]{8}(-[\w]{4}){3}-[\w]{12}'

FPR_URL = 'https://fpr.archivematica.org/fpr/api/v2/'
FPR_VERIFY_CERT = True

ALLOWED_HOSTS = ('*')
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
TEXTAREA_ATTRS = {'rows': '4', 'class': 'span11'}
TEXTAREA_WITH_HELP_ATTRS = {'rows': '4', 'class': 'span11 has_contextual_help'}
INPUT_ATTRS = {'class': 'span11'}
INPUT_WITH_HELP_ATTRS = {'class': 'span11 has_contextual_help'}

SHARED_DIRECTORY = config.get('shared_directory', default='/var/archivematica/sharedDirectory/')
WATCH_DIRECTORY = config.get('watch_directory', default='/var/archivematica/sharedDirectory/watchedDirectories/')
ELASTICSEARCH_SERVER = config.get('elasticsearch_server', default='127.0.0.1:9200')
