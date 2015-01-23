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

from archivematicaMoveSIP import moveSIP
import sys

# dashboard
from main.models import SIP, Transfer

from sanitizeNames import sanitizePath

DetoxDic={}

if __name__ == '__main__':
    SIPDirectory = sys.argv[1]
    sipUUID =  sys.argv[2]
    date = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    unitType = sys.argv[5]
    #os.path.abspath(SIPDirectory)

    #remove trailing slash
    if SIPDirectory[-1] == "/":
        SIPDirectory = SIPDirectory[:-1]
    
    
    if unitType == "SIP": 
        klass = SIP
        locationColumn = 'currentpath'
    elif unitType == "Transfer":
        klass = Transfer
        locationColumn = 'currentlocation'
    else:
        print >>sys.stderr, "invalid unit type: ", unitType
        exit(1)
    dst = sanitizePath(SIPDirectory)
    if SIPDirectory != dst:
        dst = dst.replace(sharedDirectoryPath, "%sharedPath%", 1) + "/"
        print SIPDirectory.replace(sharedDirectoryPath, "%sharedPath%", 1) + " -> " + dst

        unit = klass.objects.get(uuid=sipUUID)
        setattr(unit, locationColumn, dst)
        unit.save()
