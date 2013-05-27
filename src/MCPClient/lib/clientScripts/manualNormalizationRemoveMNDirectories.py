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
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseFunctions
import databaseInterface

SIPDirectory = sys.argv[1]
manual_normalization_dir = os.path.join(SIPDirectory, "objects", "manualNormalization")
access_dir = os.path.join(manual_normalization_dir, "access")
preservation_dir = os.path.join(manual_normalization_dir, "preservation")

global errorCount
errorCount = 0

if os.path.isdir(manual_normalization_dir) and not errorCount:
    # Delete normalization.csv if present
    normalization_csv = os.path.join(manual_normalization_dir, 'normalization.csv')
    if os.path.isfile(normalization_csv):
        os.remove(normalization_csv)
        # Need SIP UUID to get file UUID to remove file in DB
        sipUUID = SIPDirectory[-37:-1] # Account for trailing /
        sql = """SELECT fileUUID 
                 FROM Files 
                 WHERE removedTime = 0 AND 
                    Files.originalLocation LIKE '%normalization.csv' AND 
                    SIPUUID='{sipUUID}';""".format(sipUUID=sipUUID)
        rows = databaseInterface.queryAllSQL(sql)
        fileUUID = rows[0][0]
        databaseFunctions.fileWasRemoved(fileUUID)

    # Delete empty access, preservation, and manual normalization dir
    for directory in (access_dir, preservation_dir, manual_normalization_dir):
        try:
            os.rmdir(directory)
        except Exception as e:
            print >>sys.stderr, "{0} could not be deleted: {1}".format(
                directory, e.args)
            errorCount+= 1

exit(errorCount)
