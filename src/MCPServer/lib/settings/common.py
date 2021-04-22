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
from __future__ import division

import json
import logging
import logging.config
import math
import multiprocessing
import os

from six import StringIO

from appconfig import Config, process_search_enabled, process_watched_directory_interval
import email_settings

CONFIG_MAPPING = {
    # [MCPServer]
    "shared_directory": {
        "section": "MCPServer",
        "option": "sharedDirectory",
        "type": "string",
    },
    "processing_xml_file": {
        "section": "MCPServer",
        "option": "processingXMLFile",
        "type": "string",
    },
    "gearman_server": {
        "section": "MCPServer",
        "option": "MCPArchivematicaServer",
        "type": "string",
    },
    "watch_directory": {
        "section": "MCPServer",
        "option": "watchDirectoryPath",
        "type": "string",
    },
    "processing_directory": {
        "section": "MCPServer",
        "option": "processingDirectory",
        "type": "string",
    },
    "rejected_directory": {
        "section": "MCPServer",
        "option": "rejectedDirectory",
        "type": "string",
    },
    "wait_on_auto_approve": {
        "section": "MCPServer",
        "option": "waitOnAutoApprove",
        "type": "int",
    },
    "watch_directory_method": {
        "section": "MCPServer",
        "option": "watch_directory_method",
        "type": "string",
    },
    "watch_directory_interval": {
        "section": "MCPServer",
        "process_function": process_watched_directory_interval,
    },
    "secret_key": {
        "section": "MCPServer",
        "option": "django_secret_key",
        "type": "string",
    },
    "search_enabled": {
        "section": "MCPServer",
        "process_function": process_search_enabled,
    },
    "batch_size": {"section": "MCPServer", "option": "batch_size", "type": "int"},
    "concurrent_packages": {
        "section": "MCPServer",
        "option": "concurrent_packages",
        "type": "int",
    },
    "rpc_threads": {"section": "MCPServer", "option": "rpc_threads", "type": "int"},
    "worker_threads": {
        "section": "MCPServer",
        "option": "worker_threads",
        "type": "int",
    },
    "storage_service_client_timeout": {
        "section": "MCPServer",
        "option": "storage_service_client_timeout",
        "type": "float",
    },
    "storage_service_client_quick_timeout": {
        "section": "MCPServer",
        "option": "storage_service_client_quick_timeout",
        "type": "float",
    },
    "prometheus_bind_address": {
        "section": "MCPServer",
        "option": "prometheus_bind_address",
        "type": "string",
    },
    "prometheus_bind_port": {
        "section": "MCPServer",
        "option": "prometheus_bind_port",
        "type": "string",
    },
    "time_zone": {"section": "MCPServer", "option": "time_zone", "type": "string"},
    # [client]
    "db_engine": {"section": "client", "option": "engine", "type": "string"},
    "db_name": {"section": "client", "option": "database", "type": "string"},
    "db_user": {"section": "client", "option": "user", "type": "string"},
    "db_password": {"section": "client", "option": "password", "type": "string"},
    "db_host": {"section": "client", "option": "host", "type": "string"},
    "db_port": {"section": "client", "option": "port", "type": "string"},
}


CONFIG_MAPPING.update(email_settings.CONFIG_MAPPING)

CONFIG_DEFAULTS = """[MCPServer]
MCPArchivematicaServer = localhost:4730
watchDirectoryPath = /var/archivematica/sharedDirectory/watchedDirectories/
sharedDirectory = /var/archivematica/sharedDirectory/
processingDirectory = /var/archivematica/sharedDirectory/currentlyProcessing/
rejectedDirectory = %%sharedPath%%rejected/
watch_directory_method = poll
watch_directory_interval = 1
processingXMLFile = processingMCP.xml
waitOnAutoApprove = 0
search_enabled = true
batch_size = 128
rpc_threads = 4
storage_service_client_timeout = 86400
storage_service_client_quick_timeout = 5
prometheus_bind_address =
prometheus_bind_port =
time_zone = UTC

[client]
user = archivematica
password = demo
host = localhost
database = MCP
port = 3306
engine = django.db.backends.mysql

[email]
backend = django.core.mail.backends.console.EmailBackend
host = smtp.gmail.com
host_password =
host_user = your_email@example.com
port = 587
ssl_certfile =
ssl_keyfile =
use_ssl = False
use_tls = True
file_path =
default_from_email = webmaster@example.com
subject_prefix = [Archivematica]
timeout = 300
#server_email =
"""


config = Config(env_prefix="ARCHIVEMATICA_MCPSERVER", attrs=CONFIG_MAPPING)
config.read_defaults(StringIO(CONFIG_DEFAULTS))
config.read_files(
    [
        "/etc/archivematica/archivematicaCommon/dbsettings",
        "/etc/archivematica/MCPServer/serverConfig.conf",
    ]
)


DATABASES = {
    "default": {
        "ENGINE": config.get("db_engine"),
        "NAME": config.get("db_name"),
        "USER": config.get("db_user"),
        "PASSWORD": config.get("db_password"),
        "HOST": config.get("db_host"),
        "PORT": config.get("db_port"),
        "CONN_MAX_AGE": 3600,  # 1 hour
    }
}

# These are all the apps that we need so we can use the models in the
# Dashboard.
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "main",
    "components.administration",
    "fpr",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get(
    "secret_key", default="e7b-$#-3fgu)j1k01)3tp@^e0=yv1hlcc4k-b6*ap^zezv2$48"
)

USE_TZ = True
TIME_ZONE = config.get("time_zone")

# Configure logging manually
LOGGING_CONFIG = None

# Location of the logging configuration file that we're going to pass to
# `logging.config.fileConfig` unless it doesn't exist.
LOGGING_CONFIG_FILE = "/etc/archivematica/serverConfig.logging.json"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(levelname)-8s %(threadName)s %(asctime)s %(module)s:%(funcName)s:%(lineno)d:  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        }
    },
    "loggers": {"archivematica": {"level": "DEBUG"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

if os.path.isfile(LOGGING_CONFIG_FILE):
    with open(LOGGING_CONFIG_FILE, "rt") as f:
        LOGGING = logging.config.dictConfig(json.load(f))
else:
    logging.config.dictConfig(LOGGING)


def concurrent_packages_default():
    """Default to 1/2 of CPU count, rounded up."""
    cpu_count = multiprocessing.cpu_count()
    return int(math.ceil(cpu_count / 2))


SHARED_DIRECTORY = config.get("shared_directory")
WATCH_DIRECTORY = config.get("watch_directory")
REJECTED_DIRECTORY = config.get("rejected_directory")
PROCESSING_DIRECTORY = config.get("processing_directory")
PROCESSING_XML_FILE = config.get("processing_xml_file")
GEARMAN_SERVER = config.get("gearman_server")
WAIT_ON_AUTO_APPROVE = config.get("wait_on_auto_approve")
WATCH_DIRECTORY_METHOD = config.get("watch_directory_method")
WATCH_DIRECTORY_INTERVAL = config.get("watch_directory_interval")
SEARCH_ENABLED = config.get("search_enabled")
BATCH_SIZE = config.get("batch_size")
CONCURRENT_PACKAGES = config.get(
    "concurrent_packages", default=concurrent_packages_default()
)
RPC_THREADS = config.get("rpc_threads")
WORKER_THREADS = config.get("worker_threads", default=multiprocessing.cpu_count() + 1)

STORAGE_SERVICE_CLIENT_TIMEOUT = config.get("storage_service_client_timeout")
STORAGE_SERVICE_CLIENT_QUICK_TIMEOUT = config.get(
    "storage_service_client_quick_timeout"
)
PROMETHEUS_BIND_ADDRESS = config.get("prometheus_bind_address")
try:
    PROMETHEUS_BIND_PORT = int(config.get("prometheus_bind_port"))
except ValueError:
    PROMETHEUS_ENABLED = False
else:
    PROMETHEUS_ENABLED = True

# Apply email settings
globals().update(email_settings.get_settings(config))
