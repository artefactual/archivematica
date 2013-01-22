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
import os
import sys
#sys.path.append("/usr/lib/archivematica/archivematicaCommon")



#"%SIPUUID%" "%SIPName%" "%SIPDirectory%" "%fileUUID%" "%filePath%"
SIPDirectory = sys.argv[1]
accessDir = os.path.join(SIPDirectory, "objects/manualNormalization/access")
preservationDir = os.path.join(SIPDirectory, "objects/manualNormalization/preservation")
manualNormalizationDir = os.path.join(SIPDirectory, "objects/manualNormalization")

errorCount = 0


if os.path.isdir(accessDir):
    try:
        os.rmdir(accessDir)
    except Exception as inst:
        print type(inst)     # the exception instance
        print inst.args
        errorCount+= 1

if os.path.isdir(preservationDir):
    try:
        os.rmdir(preservationDir)
    except Exception as inst:
        print type(inst)     # the exception instance
        print inst.args
        errorCount+= 1

if os.path.isdir(manualNormalizationDir) and not errorCount:
    try:
        os.rmdir(manualNormalizationDir)
    except Exception as inst:
        print type(inst)     # the exception instance
        print inst.args
        errorCount+= 1

exit(errorCount)
