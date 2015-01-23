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
# archivematicaCommon
from fileOperations import updateSizeAndChecksum

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-p",  "--filePath",          action="store", dest="filePath", default="")
    parser.add_option("-d",  "--date",              action="store", dest="date", default="")
    parser.add_option("-u",  "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    (opts, args) = parser.parse_args()

    updateSizeAndChecksum(opts.fileUUID, \
                     opts.filePath, \
                     opts.date, \
                     opts.eventIdentifierUUID)
