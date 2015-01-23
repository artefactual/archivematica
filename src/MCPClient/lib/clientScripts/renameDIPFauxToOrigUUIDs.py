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
import uuid
import shutil
# archivematicaCommon
import databaseInterface

if __name__ == '__main__':
    unitUUID = sys.argv[1]
    filePath = sys.argv[2]
    
    uuidLen = 36
    basename = os.path.basename(filePath)
    fileFauxUUID = basename[:uuidLen]
    fileName = basename[uuidLen:]
    dirname = os.path.dirname(filePath)
    
    sql = """SELECT fileUUID FROM FauxFileIDsMap WHERE fauxSIPUUID='%s' AND fauxFileUUID='%s';""" % (unitUUID, fileFauxUUID)
    rows = databaseInterface.queryAllSQL(sql)
    if len(rows) != 1:
        print >>sys.stderr, "Wrong rows returned", sql, rows
        exit(-1)
    originalFileUUID = rows[0][0]
    
    dst = os.path.join(dirname, originalFileUUID + fileName)
    print basename, " -> ", originalFileUUID + fileName
    shutil.move(filePath, dst)