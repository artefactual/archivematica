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
import lxml.etree as etree
# archivematicaCommon
from fileOperations import updateFileLocation
from fileOperations import renameAsSudo

def verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory="./"):
    print metsFile
    DSpaceMets = "metadata/submissionDocumentation/DSpaceMets"
    try:
        path = os.path.join(transferDirectory, DSpaceMets)
        if not os.path.isdir(path):
            os.mkdir(path)
    except:
        print "error creating DSpaceMets directory."
    exitCode = 0

    metsDirectory = os.path.basename(os.path.dirname(metsFile))

    if metsDirectory == "DSpace_export":
        outputDirectory = path
    else:
        outputDirectory = os.path.join(path, metsDirectory)
        if not os.path.isdir(outputDirectory):
            os.mkdir(outputDirectory)

    dest = os.path.join(outputDirectory, "mets.xml")
    renameAsSudo(metsFile, dest)

    src = metsFile.replace(transferDirectory, "%transferDirectory%")
    dst = dest.replace(transferDirectory, "%transferDirectory%")
    eventDetail = ""
    eventOutcomeDetailNote = "moved from=\"" + src + "\"; moved to=\"" + dst + "\""
    updateFileLocation(src, dst, "movement", date, eventDetail, transferUUID=transferUUID, eventOutcomeDetailNote = eventOutcomeDetailNote)

    return exitCode



if __name__ == '__main__':
    metsFile = sys.argv[1]
    date = sys.argv[2]
    taskUUID = sys.argv[3]
    transferDirectory = sys.argv[4]
    transferUUID = sys.argv[5]


    ret = verifyMetsFileSecChecksums(metsFile, date, taskUUID, transferDirectory, transferUUID, relativeDirectory=os.path.dirname(metsFile) + "/")
    quit(ret)
