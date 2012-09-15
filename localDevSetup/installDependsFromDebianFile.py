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
# @subpackage archivematicaDev
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

#Depends: ${shlibs:Depends}, ${misc:Depends}, libapache2-mod-wsgi, python-django, python-django-doc
import os
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from executeOrRunSubProcess import executeOrRun
excludePackages = ["sip-creation-tools", "sanitize-names"]


filePath = sys.argv[1]
if not os.path.isfile(filePath):
    print >>sys.stderr, "File doesn't exist."
    exit(2)
f = open(filePath, 'r')

line = f.readline()
while not line.startswith("Depends:"):
    line = f.readline()



for part in line.split(","):
    part = part.strip()
    if part.find("${shlibs:Depends}") != -1 or \
        part.find("${misc:Depends}") != -1:
        continue
    if part.startswith("archivematica"):
        continue

    if part in excludePackages:
        continue

    print sys.argv[1]
    print "Attempting Install/Update of: ", part
    command = "sudo apt-get install -y " + part
    exitCode, stdOut, stdError = executeOrRun("command", command, printing=False)
    if exitCode:
        print "exitCode:", exitCode
        print stdOut
        print >>sys.stderr, stdError
    #else:
        #print "OK"
