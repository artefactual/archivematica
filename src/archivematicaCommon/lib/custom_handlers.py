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
            }
        },
        'loggers': {
            root: {  # 'archivematica'
                'handlers': ['logfile'],
                'level': level,
                'propagate': False,
            },
            name: {  # 'archivematica.mcp.client.script_name'
                'handlers': ['logfile'],
                'level': level,
                'propagate': False,
            },
        },
        'root': {  # Everything else
            'handlers': ['logfile'],
            'level': 'WARNING',
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(name)
    return logger
