import logging
import logging.config
import os
import sys


STANDARD_FORMAT = "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(os.path.basename(sys.argv[0]))


def get_script_logger(name, formatter=SCRIPT_FILE_FORMAT, root="archivematica", level=logging.INFO):

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'fmt': {
                'format': formatter,
            },
        },
        'handlers': {
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
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(name)
    return logger
