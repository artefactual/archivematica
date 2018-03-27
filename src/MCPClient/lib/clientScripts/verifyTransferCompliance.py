#!/usr/bin/env python2

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
from __future__ import print_function
import os
import sys
from verifySIPCompliance import checkDirectory

requiredDirectories = ["objects",
                       "logs",
                       "metadata",
                       "metadata/submissionDocumentation"]
allowableFiles = ["processingMCP.xml"]


def verifyDirectoriesExist(SIPDir, ret=0):
    for directory in requiredDirectories:
        if not os.path.isdir(os.path.join(SIPDir, directory)):
            print("Required Directory Does Not Exist: " + directory, file=sys.stderr)
            ret += 1
    return ret


def verifyNothingElseAtTopLevel(SIPDir, ret=0):
    for entry in os.listdir(SIPDir):
        if os.path.isdir(os.path.join(SIPDir, entry)):
            if entry not in requiredDirectories:
                print("Error, directory exists: " + entry, file=sys.stderr)
                ret += 1
        else:
            if entry not in allowableFiles:
                print("Error, file exists: " + entry, file=sys.stderr)
                ret += 1
    return ret


def verifyThereAreFiles(SIPDir, ret=0):
    """
    Make sure there are files in the transfer
    """
    if not any(
        files
        for (_, _, files) in os.walk(SIPDir)
    ):
        print("Error, no files found", file=sys.stderr)
        ret += 1

    return ret


if __name__ == '__main__':
    SIPDir = sys.argv[1]
    ret = verifyDirectoriesExist(SIPDir)
    ret = verifyNothingElseAtTopLevel(SIPDir, ret)
    ret = checkDirectory(SIPDir, ret)
    ret = verifyThereAreFiles(SIPDir, ret)
    if ret != 0:
        import time
        time.sleep(10)
    quit(ret)
