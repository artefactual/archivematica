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
import lxml.etree as etree
import MySQLdb
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory="./"):
    print metsFile
    DspaceLicenses = "metadata/submissionDocumentation/DspaceLicenses"
    try:
        path = os.path.join(transferDirectory, DspaceLicenses)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        print "error creating DspaceLicenses directory."
    exitCode = 0
    tree = etree.parse(metsFile)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}fileSec/{http://www.loc.gov/METS/}fileGrp"):
        #print etree.tostring(item)
        #print item

        USE = item.get("USE")
        if USE == "TEXT":
            for item2 in item:
                if item2.tag == "{http://www.loc.gov/METS/}file":
                    for item3 in item2:
                        if item3.tag == "{http://www.loc.gov/METS/}FLocat":
                            fileLocation = item3.get("{http://www.w3.org/1999/xlink}href")
                            fileFullPath = os.path.join(relativeDirectory, fileLocation)

                            dbLocation = fileFullPath.replace(transferDirectory, "%transferDirectory%")
                            sql = """UPDATE Files SET fileGrpUse = 'text/ocr' WHERE currentLocation = '%s' AND transferUUID = '%s';""" % (MySQLdb.escape_string(dbLocation), transferUUID)
                            databaseInterface.runSQL(sql)
    return exitCode



if __name__ == '__main__':
    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]
    transferDirectory = sys.argv[4]
    transferUUID = sys.argv[5]


    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
