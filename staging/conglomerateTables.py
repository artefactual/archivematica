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
# @subpackage transcoder
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import uuid
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import traceback
import lxml.etree as etree
from optparse import OptionParser

databaseInterface.printSQL = True


#tables = ['FileIDsByFitsDROIDIdentificationPUID', 'FileIDsByFitsDROIDMimeType', 'FileIDsByFitsFfidentMimetype', 'FileIDsByFitsFileUtilityFormat', 'FileIDsByFitsFileUtilityMimetype', 'FileIDsByFitsFitsFormat', 'FileIDsByFitsFitsMimetype', 'FileIDsByFitsJhoveFormat', 'FileIDsByFitsJhoveMimeType']
tables = ['FileIDsByExtension']

newTable= """
CREATE TABLE `FileIDsBySingleID` (
  `pk` varchar(50) PRIMARY KEY,
  `fileID` varchar(50) DEFAULT NULL,
  FOREIGN KEY (`fileID`) REFERENCES `FileIDs` (`pk`),
  `id` TEXT,
  `replaces` varchar(50) DEFAULT NULL,
  tool  TEXT,
  toolVersion TEXT,
  INDEX USING HASH (tool(50)),
  INDEX USING HASH (toolVersion(50)),
  `lastModified` TIMESTAMP DEFAULT NOW()
)DEFAULT CHARSET=utf8;

"""

if __name__ == '__main__':
    for table in tables:
        sql = """SELECT pk, FileIDs, Extension FROM %s;""" % (table)
        rows = databaseInterface.queryAllSQL(sql)
        for row in rows:
            pk, FileIDs, id = row
            databaseInterface.runSQL("""INSERT INTO FileIDsBySingleID (pk, fileID, id, tool) VALUES ('%s', '%s', '%s', '%s')""" % (pk, FileIDs, id, table))
            