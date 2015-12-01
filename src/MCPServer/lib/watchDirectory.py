#!/usr/bin/env python2

import logging
import os
import time
import threading
import sys

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from django_mysqlpool import auto_close_db
from archivematicaFunctions import unicodeToStr

from utils import log_exceptions

LOGGER = logging.getLogger('archivematica.mcp.server')

class archivematicaWatchDirectory:
    """Watches for new files/directories to process in a watched directory. Directories are defined in the WatchedDirectoriesTable.""" 
    def __init__(self, directory, 
                 variablesAdded=None, 
                 callBackFunctionAdded=None, 
                 variablesRemoved=None, 
                 callBackFunctionRemoved=None, 
                 alertOnDirectories=True, 
                 alertOnFiles=True, 
                 interval=1, 
                 threaded=True):
        self.run = False
        self.variablesAdded = variablesAdded
        self.callBackFunctionAdded = callBackFunctionAdded 
        self.variablesRemoved = variablesRemoved 
        self.callBackFunctionRemoved = callBackFunctionRemoved
        self.directory = directory
        self.alertOnDirectories = alertOnDirectories
        self.alertOnFiles = alertOnFiles
        self.interval= interval
        
        if not os.path.isdir(directory):
            os.makedirs(directory, mode=770)
        
        if threaded:
            t = threading.Thread(target=self.start)
            t.daemon = True
            t.start()
        else:
            self.start()

    @log_exceptions
    @auto_close_db
    def start(self):
        """Based on polling example: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html"""
        self.run = True
        LOGGER.info('Watching directory %s (Files: %s)', self.directory, self.alertOnFiles)
        before = dict ([(f, None) for f in os.listdir (self.directory)])
        while self.run:
            time.sleep (self.interval)
            after = dict ([(f, None) for f in os.listdir (self.directory)])
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
            if added: 
                LOGGER.debug('Added %s', added)
                for i in added:
                    i = unicodeToStr(i)
                    directory = unicodeToStr(self.directory)
                    self.event(os.path.join(directory, i), self.variablesAdded, self.callBackFunctionAdded)
            if removed:
                LOGGER.debug('Removed %s', removed)
                for i in removed:
                    i = unicodeToStr(i)
                    directory = unicodeToStr(self.directory)
                    self.event(os.path.join(directory, i), self.variablesRemoved, self.callBackFunctionRemoved)
            before = after
    
    def event(self, path, variables, function):
        if not function:
            return
        if os.path.isdir(path) and self.alertOnDirectories:
            function(path, variables)
        if os.path.isfile(path) and self.alertOnFiles:
            function(path, variables)
    
    def stop(self):
        self.run = False
            
def testCallBackFunction(path, variables):
    print path, variables
    

if __name__ == '__main__':
    print "example use"
    directory = "/tmp/"
    #directory = "."
    variablesOnAdded = {"something":"yes", "nothing":"no"}
    archivematicaWatchDirectory(directory, threaded=False, variablesAdded=variablesOnAdded, callBackFunctionAdded=testCallBackFunction, callBackFunctionRemoved=testCallBackFunction)
