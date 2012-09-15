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

import os
import sys
exitCode = 0


def removeEmptyDirectories(path):
    if not os.path.isdir(path):
        print "Not a directory: ", path
        exit(1)
    empty = True
    for leaf in os.listdir(path):
        fullPath = os.path.join(path, leaf)
        try:
            if os.path.isdir(fullPath):
                if not removeEmptyDirectories(fullPath):
                    empty = False
            else:
                empty = False
        except:
            print >>sys.stderr, "Error with path:", fullPath
            exitCode+=1
    if empty == True:
        try:
            os.rmdir(path)
            print "removing empty directory:", path
        except:
            print >>sys.stderr, "Error removing:", path
    return empty



if __name__ == '__main__':
    path = sys.argv[1]
    removeEmptyDirectories(path)
    exit(exitCode)
