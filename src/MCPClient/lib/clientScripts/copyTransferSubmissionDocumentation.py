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
import shutil
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface


if __name__ == '__main__':
    sipUUID = sys.argv[1]
    submissionDocumentationDirectory = sys.argv[2]
    sharedPath = sys.argv[3]

    sql = """SELECT Transfers.currentLocation FROM Transfers WHERE Transfers.transferUUID IN (SELECT transferUUID FROM Files WHERE  removedTime = 0 AND sipUUID =  '%s');""" % (sipUUID)
    print sql
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        #print row
        transferLocation = row[0].replace("%sharedPath%", sharedPath)
        transferNameUUID = os.path.basename(os.path.abspath(transferLocation))
        src = os.path.join(transferLocation, "metadata/submissionDocumentation")
        dst = os.path.join(submissionDocumentationDirectory, "transfer-%s" % (transferNameUUID))
        print >>sys.stderr, src, " -> ", dst
        shutil.copytree(src, dst)
        row = c.fetchone()
    sqlLock.release()
