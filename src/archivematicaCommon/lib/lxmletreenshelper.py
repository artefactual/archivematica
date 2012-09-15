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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$
import os
import sys
requiredDirectories = ["objects", \
                       "logs", \
                       "metadata",\
                       "metadata/submissionDocumentation"]

def createStructuredDirectory(SIPDir):
    for directory in requiredDirectories:
        path = os.path.join(SIPDir, directory)
        if not os.path.isdir(path):
            os.makedirs(path)

if __name__ == '__main__':
    SIPDir = sys.argv[1]
    createStructuredDirectory(SIPDir)
