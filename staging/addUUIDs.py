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
# @author Joseph Perry <joseph@artefactual.com>

import sys
import os
import uuid

def addUUIDs(target):
    replace = " = '';\n"
    basename = os.path.basename(target)
    index = basename.rfind(".")
    if index == -1:
        return
    output = os.path.join(os.path.dirname(target), basename[:index] + "_UUIDs" + basename[index:])
    f = open(target, 'r')
    content = f.read()
    index = content.find(replace)
    while index != -1:
        content = content.replace(replace, " = '%s';\n" % uuid.uuid4().__str__(), 1)
        index = content.find(replace)
    
    f2 = open(output, 'w')
    f2.write(content)
    
    f.close()
    f2.close()
    
    

if __name__ == '__main__':
	target = sys.argv[1]
	addUUIDs(target)
