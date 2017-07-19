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
    # [MCPServer]
    'shared_directory': {'section': 'MCPServer', 'option': 'sharedDirectory', 'type': 'string'},
    'processing_xml_file': {'section': 'MCPServer', 'option': 'processingXMLFile', 'type': 'string'},
    'gearman_server': {'section': 'MCPServer', 'option': 'MCPArchivematicaServer', 'type': 'string'},
    'watch_directory': {'section': 'MCPServer', 'option': 'watchDirectoryPath', 'type': 'string'},
    'processing_directory': {'section': 'MCPServer', 'option': 'processingDirectory', 'type': 'string'},
    'rejected_directory': {'section': 'MCPServer', 'option': 'rejectedDirectory', 'type': 'string'},
    'wait_on_auto_approve': {'section': 'MCPServer', 'option': 'waitOnAutoApprove', 'type': 'int'},
    'watch_directory_interval': {'section': 'MCPServer', 'option': 'watchDirectoriesPollInterval', 'type': 'int'},
    'secret_key': {'section': 'MCPServer', 'option': 'django_secret_key', 'type': 'string'},

    # [Protocol]
    'limit_task_threads': {'section': 'Protocol', 'option': 'limitTaskThreads', 'type': 'int'},
    'limit_task_threads_sleep': {'section': 'Protocol', 'option': 'limitTaskThreadsSleep', 'type': 'float'},
    'limit_gearman_conns': {'section': 'Protocol', 'option': 'limitGearmanConnections', 'type': 'int'},
    'reserved_as_task_processing_threads': {'section': 'Protocol', 'option': 'reservedAsTaskProcessingThreads', 'type': 'int'},

    # [client]
    'db_engine': {'section': 'client', 'option': 'engine', 'type': 'string'},
    'db_name': {'section': 'client', 'option': 'database', 'type': 'string'},
    'db_user': {'section': 'client', 'option': 'user', 'type': 'string'},
    'db_password': {'section': 'client', 'option': 'password', 'type': 'string'},
    'db_host': {'section': 'client', 'option': 'host', 'type': 'string'},
    'db_port': {'section': 'client', 'option': 'port', 'type': 'string'},
    'db_pool_max_overflow': {'section': 'client', 'option': 'max_overflow', 'type': 'string'},
}


CONFIG_DEFAULTS = """[MCPServer]
MCPArchivematicaServer = localhost:4730
watchDirectoryPath = /var/archivematica/sharedDirectory/watchedDirectories/
sharedDirectory = /var/archivematica/sharedDirectory/
processingDirectory = /var/archivematica/sharedDirectory/currentlyProcessing/
rejectedDirectory = %%sharedPath%%rejected/
watchDirectoriesPollInterval = 1
processingXMLFile = processingMCP.xml
waitOnAutoApprove = 0

[Protocol]
delimiter = <!&\delimiter/&!>
limitGearmanConnections = 10000
limitTaskThreads = 75
limitTaskThreadsSleep = 0.2
reservedAsTaskProcessingThreads = 8

[client]
user = archivematica
password = demo
host = localhost
database = MCP
max_overflow = 40
port = 3306
engine = django_mysqlpool.backends.mysqlpool
"""


config = Config(env_prefix='ARCHIVEMATICA_MCPSERVER', attrs=CONFIG_MAPPING)
config.read_defaults(StringIO.StringIO(CONFIG_DEFAULTS))
config.read_files([
    '/etc/archivematica/archivematicaCommon/dbsettings',
    '/etc/archivematica/serverConfig.conf',
])


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

MYSQLPOOL_BACKEND = 'QueuePool'
MYSQLPOOL_ARGUMENTS = {
    'use_threadlocal': False,
    'max_overflow': config.get('db_pool_max_overflow'),
}

CONN_MAX_AGE = 14400

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('secret_key', default='e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48')

USE_TZ = True
TIME_ZONE = 'UTC'

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
        'verboselogfile': {
            'level': 'DEBUG',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPServer/MCPServer.debug.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 4 MiB
        },
        'logfile': {
            'level': 'INFO',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPServer/MCPServer.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 4 MiB
        },
    },
    'loggers': {
        'archivematica': {
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['logfile', 'verboselogfile'],
        'level': 'WARNING',
    },
}


SHARED_DIRECTORY = config.get('shared_directory')
WATCH_DIRECTORY = config.get('watch_directory')
REJECTED_DIRECTORY = config.get('rejected_directory')
PROCESSING_DIRECTORY = config.get('processing_directory')
PROCESSING_XML_FILE = config.get('processing_xml_file')
GEARMAN_SERVER = config.get('gearman_server')
WAIT_ON_AUTO_APPROVE = config.get('wait_on_auto_approve')
WATCH_DIRECTORY_INTERVAL = config.get('watch_directory_interval')
LIMIT_TASK_THREADS = config.get('limit_task_threads')
LIMIT_TASK_THREADS_SLEEP = config.get('limit_task_threads_sleep')
LIMIT_GEARMAN_CONNS = config.get('limit_gearman_conns')
RESERVED_AS_TASK_PROCESSING_THREADS = config.get('reserved_as_task_processing_threads')
