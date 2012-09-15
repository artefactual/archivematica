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
from optparse import OptionParser
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface


def main(sipUUID, transfersDirectory, sharedPath=""):
    if not os.path.exists(transfersDirectory):
        os.makedirs(transfersDirectory)

    exitCode = 0
    sql = """SELECT Files.transferUUID, Transfers.currentLocation FROM Files
        JOIN Transfers on Transfers.transferUUID = Files.transferUUID
        WHERE sipUUID = '%s'
        GROUP BY Files.transferUUID;""" % (sipUUID)

    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        try:
            transferUUID = row[0]
            transferPath = row[1]
            if sharedPath != "":
                transferPath = transferPath.replace("%sharedPath%", sharedPath, 1)
            transferBasename = os.path.basename(os.path.abspath(transferPath))
            transferMetaDestDir = os.path.join(transfersDirectory, transferBasename)
            if not os.path.exists(transferMetaDestDir):
                os.makedirs(transferMetaDestDir)
                shutil.copytree(transferPath + "logs", os.path.join(transferMetaDestDir, "logs"))
                print "copied: ", transferPath + "logs", " -> ", os.path.join(transferMetaDestDir, "logs")
                shutil.copytree(transferPath + "metadata", os.path.join(transferMetaDestDir, "metadata"))
                print "copied: ", transferPath + "metadata", " -> ", os.path.join(transferMetaDestDir, "metadata")

        except Exception as inst:
            print >>sys.stderr, type(inst)
            print >>sys.stderr, inst.args
            print >>sys.stderr, "Error with transfer: ", row
            exitCode += 1
        row = c.fetchone()

    sqlLock.release()
    exit(exitCode)

if __name__ == '__main__':
    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)
    parser = OptionParser()
    parser.add_option("-s",  "--sipDirectory", action="store", dest="sipDirectory", default="")
    parser.add_option("-S",  "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-p",  "--sharedPath", action="store", dest="sharedPath", default="/var/archivematica/sharedDirectory/")
    (opts, args) = parser.parse_args()


    main(opts.sipUUID, opts.sipDirectory+"metadata/transfers/", sharedPath=opts.sharedPath)
