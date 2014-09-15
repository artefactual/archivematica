import logging.handlers
import os

class GroupWriteRotatingFileHandler(logging.handlers.RotatingFileHandler):    
    def _open(self):
        prevumask = os.umask(0o002)
        try:
            rtv=logging.handlers.RotatingFileHandler._open(self)
            return rtv
        finally:
            os.umask(prevumask)
