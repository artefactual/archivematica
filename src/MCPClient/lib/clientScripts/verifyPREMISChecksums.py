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
import sys
from optparse import OptionParser

# dashboard
from main.models import File

# archivematicaCommon
import databaseFunctions
from externals.checksummingTools import sha_for_file

def verifyChecksum(fileUUID, filePath, date, eventIdentifierUUID):
    f = File.objects.get(uuid=fileUUID)

    if f.checksum in ("", "None"):
        print >>sys.stderr, "No checksum found in database for file:", fileUUID, filePath
        exit(1)
    checksumFile = sha_for_file(filePath)

    eventOutcome=""
    eventOutcomeDetailNote=""
    exitCode = 0
    if checksumFile != f.checksum:
        eventOutcomeDetailNote = str(checksumFile) + " != " + f.checksum
        eventOutcome="Fail"
        exitCode = 2
        print >>sys.stderr, "Checksums do not match:", fileUUID, filePath
        print >>sys.stderr, eventOutcomeDetailNote
    else:
        eventOutcomeDetailNote = "%s %s" % (str(checksumFile), "verified")
        eventOutcome="Pass"
        exitCode = 0

    databaseFunctions.insertIntoEvents(fileUUID=fileUUID, \
                 eventIdentifierUUID=eventIdentifierUUID, \
                 eventType="fixity check", \
                 eventDateTime=date, \
                 eventOutcome=eventOutcome, \
                 eventOutcomeDetailNote=eventOutcomeDetailNote, \
                 eventDetail="program=\"python\"; module=\"hashlib.sha256()\"")

    exit(exitCode)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-p",  "--filePath",          action="store", dest="filePath", default="")
    parser.add_option("-d",  "--date",              action="store", dest="date", default="")
    parser.add_option("-u",  "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    (opts, args) = parser.parse_args()

    verifyChecksum(opts.fileUUID, \
                     opts.filePath, \
                     opts.date, \
                     opts.eventIdentifierUUID)
