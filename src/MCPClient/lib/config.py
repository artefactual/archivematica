import os

from env_configparser import EnvConfigParser
import config


ENV_PREFIX = 'ARCHIVEMATICA_MCPCLIENT'
ENV_CONFIG_FILE = '{}_CONFIG'.format(ENV_PREFIX)
ENV_CONFIG_FILE_SEPARATOR = ':'


def _load_settings():
    config = EnvConfigParser(prefix=ENV_PREFIX)
    if ENV_CONFIG_FILE in os.environ:
        config.read(os.environ[ENV_CONFIG_FILE].split(ENV_CONFIG_FILE_SEPARATOR))
    return config


settings = _load_settings()


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(levelname)-8s  %(asctime)s  %(name)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'logfile': {
            'level': 'INFO',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPClient/MCPClient.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 20 MiB
        },
        'verboselogfile': {
            'level': 'DEBUG',
            'class': 'custom_handlers.GroupWriteRotatingFileHandler',
            'filename': '/var/log/archivematica/MCPClient/MCPClient.debug.log',
            'formatter': 'detailed',
            'backupCount': 5,
            'maxBytes': 4 * 1024 * 1024,  # 100 MiB
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
    }
}
