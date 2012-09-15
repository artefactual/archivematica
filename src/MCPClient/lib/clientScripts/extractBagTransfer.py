#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$
import shutil
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
import databaseInterface


def extract(target, destinationDirectory):
    command = """/usr/bin/7z x -bd -o"%s" "%s" """ % (destinationDirectory, target)
    exitC, stdOut, stdErr = executeOrRun("command", command, printing=False)
    if exitC != 0:
        print stdOut
        print >>sys.stderr, "Failed extraction: ", command, "\r\n", stdErr
        exit(exitC)
        
    


if __name__ == '__main__':
    target = sys.argv[1]
    transferUUID =  sys.argv[2]
    processingDirectory = sys.argv[3]
    sharedPath = sys.argv[4]
    
    basename = os.path.basename(target)
    basename = basename[:basename.rfind(".")]
    
    destinationDirectory = os.path.join(processingDirectory, basename)
    zipLocation = os.path.join(processingDirectory, os.path.basename(target))
    
    #move to processing directory
    shutil.move(target, zipLocation)
    
    #extract
    extract(zipLocation, destinationDirectory)
    
    #checkForTopLevelBag
    listdir = os.listdir(destinationDirectory)
    if len(listdir) == 1:
        internalBagName = listdir[0]
        #print "ignoring BagIt internal name: ", internalBagName  
        temp = destinationDirectory + "-tmp"
        shutil.move(destinationDirectory, temp)
        #destinationDirectory = os.path.join(processingDirectory, internalBagName)
        shutil.move(os.path.join(temp, internalBagName), destinationDirectory)
        os.rmdir(temp)
    
    #update transfer
    destinationDirectoryDB = destinationDirectory.replace(sharedPath, "%sharedPath%", 1)
    sql = """UPDATE Transfers SET currentLocation = '%s' WHERE transferUUID = '%s';""" % (destinationDirectoryDB, transferUUID)
    databaseInterface.runSQL(sql)
    
    #remove bag
    os.remove(zipLocation)

 


