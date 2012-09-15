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


import sys
import os
import uuid
import MySQLdb

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoDerivations
from fileOperations import addFileToSIP
from fileOperations import updateSizeAndChecksum
import databaseInterface


def xmlCreateFileAssociationBetween(originalFileFullPath, outputFromNormalizationFileFullPath, SIPFullPath, sipUUID, eventDetailText, eventOutcomeDetailNote, outputFileUUID=""):
    #assign file UUID

    date = databaseInterface.getUTCDate()
    if outputFileUUID == "":
        outputFileUUID = uuid.uuid4().__str__()

    originalFilePathRelativeToSIP = originalFileFullPath.replace(SIPFullPath,"%SIPDirectory%", 1)
    sql = "SELECT Files.fileUUID FROM Files WHERE removedTime = 0 AND Files.currentLocation = '" + MySQLdb.escape_string(originalFilePathRelativeToSIP) + "' AND Files.sipUUID = '" + sipUUID + "';"
    print sql
    rows = databaseInterface.queryAllSQL(sql)
    print rows
    fileUUID = rows[0][0]


    filePathRelativeToSIP = outputFromNormalizationFileFullPath.replace(SIPFullPath,"%SIPDirectory%", 1)
    addFileToSIP(filePathRelativeToSIP, outputFileUUID, sipUUID, uuid.uuid4().__str__(), date, sourceType="creation", use="preservation")
    updateSizeAndChecksum(outputFileUUID, outputFromNormalizationFileFullPath, date, uuid.uuid4().__str__())

    taskUUID = uuid.uuid4().__str__()
    insertIntoEvents(fileUUID=fileUUID, \
               eventIdentifierUUID=taskUUID, \
               eventType="normalization", \
               eventDateTime=date, \
               eventDetail=eventDetailText, \
               eventOutcome="", \
               eventOutcomeDetailNote=eventOutcomeDetailNote)

    insertIntoDerivations(sourceFileUUID=fileUUID, derivedFileUUID=outputFileUUID, relatedEventUUID=taskUUID)


if __name__ == '__main__':
    originalFileFullPath = sys.argv[1]
    outputFromNormalizationFileFullPath = sys.argv[2]
    SIPFullPath = sys.argv[3]
    SIPUUID = sys.argv[4]
    eventDetailText = sys.argv[5]
    eventOutcomeDetailNote = sys.argv[6]

    for arg in [originalFileFullPath, outputFromNormalizationFileFullPath, SIPFullPath, SIPUUID, eventDetailText, eventOutcomeDetailNote]:
        print arg
    xmlCreateFileAssociationBetween(originalFileFullPath, outputFromNormalizationFileFullPath, SIPFullPath, SIPUUID, eventDetailText, eventOutcomeDetailNote)
