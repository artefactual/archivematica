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
import sys
import os
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]

manualNormalizationPath = os.path.join(SIPDirectory, "objects", "manualNormalization")
print manualNormalizationPath 
if os.path.isdir(manualNormalizationPath):
    manualNormalizationAccessPath = os.path.join(manualNormalizationPath, "access")
    if os.path.isdir(manualNormalizationAccessPath):
        if len(os.listdir(manualNormalizationAccessPath)):
            #77a7fa46-92b9-418e-aa88-fbedd4114c9f or 055de204-6229-4200-87f7-e3c29f095017 (indicate there is an access directory
            databaseInterface.runSQL("""UPDATE UnitVariables SET microServiceChainLink = '055de204-6229-4200-87f7-e3c29f095017' WHERE unitType='SIP' AND unitUUID = '%s' AND variable = 'returnFromManualNormalized' """ % (SIPUUID) )
            exit(179)
    manualNormalizationPreservationPath = os.path.join(manualNormalizationPath, "preservation")
    if os.path.isdir(manualNormalizationPreservationPath):
        if len(os.listdir(manualNormalizationPreservationPath)):
            exit(179)
exit(0)