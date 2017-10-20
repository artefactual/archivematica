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

import StringIO

from appconfig import Config


CONFIG_MAPPING = {
    # [MCPClient]
    'shared_directory': {'section': 'MCPClient', 'option': 'sharedDirectoryMounted', 'type': 'string'},
    'processing_directory': {'section': 'MCPClient', 'option': 'processingDirectory', 'type': 'string'},
    'rejected_directory': {'section': 'MCPClient', 'option': 'rejectedDirectory', 'type': 'string'},
    'watch_directory': {'section': 'MCPClient', 'option': 'watchDirectoryPath', 'type': 'string'},
    'client_scripts_directory': {'section': 'MCPClient', 'option': 'clientScriptsDirectory', 'type': 'string'},
    'client_assets_directory': {'section': 'MCPClient', 'option': 'clientAssetsDirectory', 'type': 'string'},
    'load_supported_commands_special': {'section': 'MCPClient', 'option': 'LoadSupportedCommandsSpecial', 'type': 'boolean'},
    'gearman_server': {'section': 'MCPClient', 'option': 'MCPArchivematicaServer', 'type': 'string'},
    'number_of_tasks': {'section': 'MCPClient', 'option': 'numberOfTasks', 'type': 'int'},
    'client_modules_file': {'section': 'MCPClient', 'option': 'archivematicaClientModules', 'type': 'string'},
    'elasticsearch_server': {'section': 'MCPClient', 'option': 'elasticsearchServer', 'type': 'string'},
    'elasticsearch_timeout': {'section': 'MCPClient', 'option': 'elasticsearchTimeout', 'type': 'float'},
    'disable_search_indexing': {'section': 'MCPClient', 'option': 'disableElasticsearchIndexing', 'type': 'boolean'},
    'removable_files': {'section': 'MCPClient', 'option': 'removableFiles', 'type': 'string'},
    'temp_directory': {'section': 'MCPClient', 'option': 'temp_dir', 'type': 'string'},
    'secret_key': {'section': 'MCPClient', 'option': 'django_secret_key', 'type': 'string'},
    'clamav_server': {'section': 'MCPClient', 'option': 'clamav_server', 'type': 'string'},
    'clamav_pass_by_reference': {'section': 'MCPClient', 'option': 'clamav_pass_by_reference', 'type': 'boolean'},
    'storage_service_client_timeout': {'section': 'MCPClient', 'option': 'storage_service_client_timeout', 'type': 'float'},
    'agentarchives_client_timeout': {'section': 'MCPClient', 'option': 'agentarchives_client_timeout', 'type': 'float'},
    'clamav_client_timeout': {'section': 'MCPClient', 'option': 'clamav_client_timeout', 'type': 'float'},

    # [client]
    'db_engine': {'section': 'client', 'option': 'engine', 'type': 'string'},
    'db_name': {'section': 'client', 'option': 'database', 'type': 'string'},
    'db_user': {'section': 'client', 'option': 'user', 'type': 'string'},
    'db_password': {'section': 'client', 'option': 'password', 'type': 'string'},
    'db_host': {'section': 'client', 'option': 'host', 'type': 'string'},
    'db_port': {'section': 'client', 'option': 'port', 'type': 'string'},
}

CONFIG_DEFAULTS = """[MCPClient]
MCPArchivematicaServer = localhost:4730
sharedDirectoryMounted = /var/archivematica/sharedDirectory/
watchDirectoryPath = /var/archivematica/sharedDirectory/watchedDirectories/
processingDirectory = /var/archivematica/sharedDirectory/currentlyProcessing/
rejectedDirectory = %%sharedPath%%rejected/
archivematicaClientModules = /usr/lib/archivematica/MCPClient/archivematicaClientModules
clientScriptsDirectory = /usr/lib/archivematica/MCPClient/clientScripts/
clientAssetsDirectory = /usr/lib/archivematica/MCPClient/assets/
LoadSupportedCommandsSpecial = True
numberOfTasks = 0
elasticsearchServer = localhost:9200
elasticsearchTimeout = 10
disableElasticsearchIndexing = False
temp_dir = /var/archivematica/sharedDirectory/tmp
removableFiles = Thumbs.db, Icon, Icon\r, .DS_Store
clamav_server = /var/run/clamav/clamd.ctl
clamav_pass_by_reference = False
storage_service_client_timeout = 86400
agentarchives_client_timeout = 300
clamav_client_timeout = 86400

[client]
user = archivematica
password = demo
host = localhost
database = MCP
port = 3306
engine = django.db.backends.mysql
"""

config = Config(env_prefix='ARCHIVEMATICA_MCPCLIENT', attrs=CONFIG_MAPPING)
config.read_defaults(StringIO.StringIO(CONFIG_DEFAULTS))
config.read_files([
    '/etc/archivematica/archivematicaCommon/dbsettings',
    '/etc/archivematica/clientConfig.conf',
])


DATABASES = {
    'default': {
        'ENGINE': config.get('db_engine'),
        'NAME': config.get('db_name'),
        'USER': config.get('db_user'),
        'PASSWORD': config.get('db_password'),
        'HOST': config.get('db_host'),
        'PORT': config.get('db_port'),

        # Recycling connections in MCPClient is not an option because this is
        # a threaded application. We need a connection pool but we don't have
        # one we can rely on at the moment - django_mysqlpool does not support
        # Py3 and seems abandoned.
        'CONN_MAX_AGE': 0,
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('secret_key', default='e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48')

USE_TZ = True
TIME_ZONE = 'UTC'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'components.accounts',
    'main',
    'components.mcp',
    'components.administration',
    'fpr',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(levelname)-8s  %(asctime)s  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'archivematica': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    }
}


SHARED_DIRECTORY = config.get('shared_directory')
PROCESSING_DIRECTORY = config.get('processing_directory')
REJECTED_DIRECTORY = config.get('rejected_directory')
WATCH_DIRECTORY = config.get('watch_directory')
CLIENT_SCRIPTS_DIRECTORY = config.get('client_scripts_directory')
CLIENT_ASSETS_DIRECTORY = config.get('client_assets_directory')
LOAD_SUPPORTED_COMMANDS_SPECIAL = config.get('load_supported_commands_special')
GEARMAN_SERVER = config.get('gearman_server')
NUMBER_OF_TASKS = config.get('number_of_tasks')
CLIENT_MODULES_FILE = config.get('client_modules_file')
DISABLE_SEARCH_INDEXING = config.get('disable_search_indexing')
REMOVABLE_FILES = config.get('removable_files')
TEMP_DIRECTORY = config.get('temp_directory')
ELASTICSEARCH_SERVER = config.get('elasticsearch_server')
ELASTICSEARCH_TIMEOUT = config.get('elasticsearch_timeout')
CLAMAV_SERVER = config.get('clamav_server')
CLAMAV_PASS_BY_REFERENCE = config.get('clamav_pass_by_reference')
CLAMAV_CLIENT_TIMEOUT = config.get('clamav_client_timeout')
STORAGE_SERVICE_CLIENT_TIMEOUT = config.get('storage_service_client_timeout')
AGENTARCHIVES_CLIENT_TIMEOUT = config.get('agentarchives_client_timeout')
