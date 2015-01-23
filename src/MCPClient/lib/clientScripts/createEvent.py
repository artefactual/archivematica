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
from optparse import OptionParser
import sys
# archivematicaCommon
from databaseFunctions import insertIntoEvents


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-t",  "--eventType",        action="store", dest="eventType", default="")
    parser.add_option("-d",  "--eventDateTime",     action="store", dest="eventDateTime", default="")
    parser.add_option("-e",  "--eventDetail",       action="store", dest="eventDetail", default="")
    parser.add_option("-o",  "--eventOutcome",      action="store", dest="eventOutcome", default="")
    parser.add_option("-n",  "--eventOutcomeDetailNote",   action="store", dest="eventOutcomeDetailNote", default="")
    parser.add_option("-u",  "--eventIdentifierUUID",      action="store", dest="eventIdentifierUUID", default="")


    (opts, args) = parser.parse_args()

    insertIntoEvents(fileUUID=opts.fileUUID, \
                     eventIdentifierUUID=opts.eventIdentifierUUID, \
                     eventType=opts.eventType, \
                     eventDateTime=opts.eventDateTime, \
                     eventDetail=opts.eventDetail, \
                     eventOutcome=opts.eventOutcome, \
                     eventOutcomeDetailNote=opts.eventOutcomeDetailNote)
