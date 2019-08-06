# -*- coding: utf-8 -*-
from __future__ import absolute_import

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


class CallbackHandler(logging.Handler):
    def __init__(self, callback, module_name=None):
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            "{}: ".format(module_name) + STANDARD_FORMAT
            if module_name
            else SCRIPT_FILE_FORMAT
        )
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


STANDARD_FORMAT = (
    "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
)
SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(
    os.path.basename(sys.argv[0])
)


def get_script_logger(
    name, formatter=SCRIPT_FILE_FORMAT, root="archivematica", level=logging.INFO
):

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"fmt": {"format": formatter}},
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "fmt",
            }
        },
        "loggers": {
            root: {"level": level},  # 'archivematica'
            name: {"level": level},  # 'archivematica.mcp.client.script_name'
        },
        "root": {"handlers": ["console"], "level": "WARNING"},  # Everything else
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(name)
    return logger
