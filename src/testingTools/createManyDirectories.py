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
# @subpackage Testing
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
try:
    max = int(sys.argv[1])
except:
    max = 950
try:
    max2 = int(sys.argv[1])
except:
    max2 = 950

def simple(i = 0, str = "."):
    while i < max:
        str = "%s/%d" % (str, i)
        os.mkdir(str)
        i +=1
    FILE = open(str + "/testfile.txt","w")
    FILE.write("testText\n")
    FILE.close()

for x in range(max2):
    dir = "./" + x.__str__()
    os.mkdir(dir)
    simple(str=dir)
