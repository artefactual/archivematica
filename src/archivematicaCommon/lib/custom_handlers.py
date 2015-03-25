import logging
import logging.handlers
import os
import sys

class GroupWriteRotatingFileHandler(logging.handlers.RotatingFileHandler):    
    def _open(self):
        prevumask = os.umask(0o002)
        try:
            rtv=logging.handlers.RotatingFileHandler._open(self)
            return rtv
        finally:
            os.umask(prevumask)

STANDARD_FORMAT = "%(levelname)-8s  %(asctime)s  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
SCRIPT_FILE_FORMAT = "{}: %(levelname)-8s  %(asctime)s  %(name)s:%(funcName)s:%(lineno)d:  %(message)s".format(os.path.basename(sys.argv[0]))


def get_script_logger(name, formatter=SCRIPT_FILE_FORMAT, logfile="/var/log/archivematica/MCPClient/client_scripts.log", root="archivematica", logsize=4194304, level=logging.INFO):
    formatter = logging.Formatter(fmt=formatter)

    root_logger = logging.getLogger(root)
    logger = logging.getLogger(name)

    root_handler = GroupWriteRotatingFileHandler(logfile, maxBytes=logsize)
    root_handler.setFormatter(formatter)
    handler = GroupWriteRotatingFileHandler(logfile, maxBytes=logsize)
    handler.setFormatter(formatter)

    root_logger.addHandler(root_handler)
    root_logger.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
