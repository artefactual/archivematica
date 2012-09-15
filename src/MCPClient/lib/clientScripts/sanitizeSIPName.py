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

#import os
from archivematicaMoveSIP import moveSIP
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
sys.path.append("/usr/lib/sanitizeNames")
from sanitizeNames import sanitizePath


DetoxDic={}

if __name__ == '__main__':
    SIPDirectory = sys.argv[1]
    sipUUID =  sys.argv[2]
    date = sys.argv[3]
    sharedDirectoryPath = sys.argv[4]
    #os.path.abspath(SIPDirectory)

    dst = sanitizePath(SIPDirectory)
    if SIPDirectory != dst:
        dst = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
        print SIPDirectory.replace(sharedDirectoryPath, "%sharedPath%", 1) + " -> " + dst
        sql =  """UPDATE SIPs SET currentPath='""" + dst + """' WHERE sipUUID='""" + sipUUID + """';"""
        databaseInterface.runSQL(sql)
