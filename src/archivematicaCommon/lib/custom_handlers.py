import logging
import logging.config
import logging.handlers
import os
import sys

class GroupWriteRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def _open(self):
        prevumask = os.umask(0o002)
        try:
            rtv = logging.handlers.RotatingFileHandler._open(self)
            return rtv
        finally:
            os.umask(prevumask)

STANDARD_FORMAT = "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(os.path.basename(sys.argv[0]))


def get_script_logger(name, formatter=SCRIPT_FILE_FORMAT, logfile="/var/log/archivematica/MCPClient/client_scripts.log", root="archivematica", logsize=4194304, level=logging.INFO):

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'fmt': {
                'format': formatter,
            },
        },
        'handlers': {
            'logfile': {
                'class': 'custom_handlers.GroupWriteRotatingFileHandler',
                'formatter': 'fmt',
                'filename': logfile,
                'maxBytes': logsize,
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'fmt',
            },
        },
        'loggers': {
            root: {  # 'archivematica'
                'level': level,
            },
            name: {  # 'archivematica.mcp.client.script_name'
                'level': level,
            },
        },
        'root': {  # Everything else
            'handlers': ['logfile'],
            'level': 'WARNING',
        },
    }

    # Don't use the `logfile` handler during testing so we don't force the
    # developer to run the suite as the archivematica user.
    try:
        if os.environ['DJANGO_SETTINGS_MODULE'] == 'settings.test':
            del logging_config['handlers']['logfile']
            logging_config['root']['handlers'] = ['console']
    except KeyError:
        pass
   
    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(name)
    return logger
