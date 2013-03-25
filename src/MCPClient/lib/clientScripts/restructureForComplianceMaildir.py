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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
import shutil



requiredDirectories = ["logs", "logs/fileMeta", "metadata", "metadata/submissionDocumentation", "objects", "objects/Maildir"]
optionalFiles = "processingMCP.xml"

def restructureMaildirDirectory(unitPath):
    for dir in requiredDirectories:
        dirPath = os.path.join(unitPath, dir)
        if not os.path.isdir(dirPath):
            os.mkdir(dirPath)
            print "creating: ", dir
    for item in os.listdir(unitPath):
        dst = os.path.join(unitPath, "objects", "Maildir") + "/."
        itemPath =  os.path.join(unitPath, item)
        if os.path.isdir(itemPath) and item not in requiredDirectories:
            shutil.move(itemPath, dst)
            print "moving directory to objects/Maildir: ", item
        elif os.path.isfile(itemPath) and item not in optionalFiles:
            shutil.move(itemPath, dst)
            print "moving file to objects/Maildir: ", item

if __name__ == '__main__':
    target = sys.argv[1]
    restructureMaildirDirectory(target)
    
