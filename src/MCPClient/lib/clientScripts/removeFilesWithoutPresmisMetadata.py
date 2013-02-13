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
import os
from optparse import OptionParser

def verifyFileUUID(fileUUID, filePath, sipDirectory):
    if fileUUID == "None":
        relativeFilePath = filePath.replace(sipDirectory, "%SIPDirectory%", 1)
        print >>sys.stderr, relativeFilePath
        os.remove(filePath)
        quit(0)


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-f",  "--inputFile",          action="store", dest="inputFile", default="")
    parser.add_option("-o",  "--sipDirectory",  action="store", dest="sipDirectory", default="")
    parser.add_option("-i",  "--fileUUID",           action="store", dest="fileUUID", default="")

    (opts, args) = parser.parse_args()

    verifyFileUUID(opts.fileUUID, opts.inputFile, opts.sipDirectory)
