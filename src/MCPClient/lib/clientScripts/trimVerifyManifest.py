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
import re
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun

transferName=""
printSubProcessOutput=True

currentDirectory = ""
fileCount = 0
exitCode = 0

for line in open('myfile','r'):
    if line.startswith(" Directory of "):
        i = line.find("/%s/" % transferName)
        if i != -1:
            currentDirectory = line[:i+len(transferName)]
    
    
    #check that it starts with a date
    if re.match('^[0-1][0-9]/[0-3][0-9]/[0-3][0-9][0-9][0-9]', line):
        #check that it's not a <DIR>
        isDir = False
        if line.find('<DIR>') != -1:
            isDir = True
        #split by whitespace
        sections = len(re.split('\s+', line))
        if len(sections) < 5:
            continue
        
        path = os.path.join(TransferDirectory, currentDirectory, sections[5]) #assumes no spaces in file name 
        
        if isDir:
            if os.path.isdir(path):
                print "Verified directory exists: ", path.replace(TransferDirectory, "%TransferDirectory%")
            else:
                print >>sys.stderr, "Directory does not exists: ", path.replace(TransferDirectory, "%TransferDirectory%")
                exitCode += 1
        else:
            if os.path.isfile(path):
                print "Verified file exists: ", path.replace(TransferDirectory, "%TransferDirectory%")
                fileCount += 1
            else:
                print >>sys.stderr, "File does not exists: ", path.replace(TransferDirectory, "%TransferDirectory%")
                exitCode += 1
if fileCount:
    quit(exitCode)
else:
    print >>sys.stderr, "No files found."
    quit(-1)
