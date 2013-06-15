#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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

# @package Archivematica
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
# @thanks to http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
import os
import time
import threading
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivematicaFunctions import unicodeToStr

from archivematicaMCP import debug
DEBUG = debug

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
    
    def start(self):
        """Based on polling example: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html"""
        self.run = True
        if DEBUG:
            print "watching directory: ", self.directory
        before = dict ([(f, None) for f in os.listdir (self.directory)])
        while self.run:
            time.sleep (self.interval)
            after = dict ([(f, None) for f in os.listdir (self.directory)])
            added = [f for f in after if not f in before]
            removed = [f for f in before if not f in after]
            if added: 
                if DEBUG:
                    print "Added: ", ", ".join (added)
                for i in added:
                    i = unicodeToStr(i)
                    directory = unicodeToStr(self.directory)
                    self.event(os.path.join(directory, i), self.variablesAdded, self.callBackFunctionAdded)
            if removed:
                if DEBUG: 
                    print "Removed: ", ", ".join (removed)
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
                  
    