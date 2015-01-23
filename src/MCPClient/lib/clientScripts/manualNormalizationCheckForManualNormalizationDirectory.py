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

# dashboard
from main.models import UnitVariable

SIPUUID = sys.argv[1]
SIPName = sys.argv[2]
SIPDirectory = sys.argv[3]

manualNormalizationPath = os.path.join(SIPDirectory, "objects", "manualNormalization")
print manualNormalizationPath 
if os.path.isdir(manualNormalizationPath):
    manualNormalizationAccessPath = os.path.join(manualNormalizationPath, "access")
    if os.path.isdir(manualNormalizationAccessPath):
        if len(os.listdir(manualNormalizationAccessPath)):
            # FIXME Workflow decisions should not be made in client scripts! It
            # is not discoverable and leads to bugs when workflow changes are
            # made and setting unit variables in client scripts is missed! This
            # should be eliminated (by having another way of setting when DIPs
            # are created) or moved to its own MSCL.
            UnitVariable.objects.filter(unittype="SIP", unituuid=SIPUUID, variable="returnFromManualNormalized").update(microservicechainlink_id="f060d17f-2376-4c0b-a346-b486446e46ce")
            exit(179)
    manualNormalizationPreservationPath = os.path.join(manualNormalizationPath, "preservation")
    if os.path.isdir(manualNormalizationPreservationPath):
        if len(os.listdir(manualNormalizationPreservationPath)):
            exit(179)
exit(0)
