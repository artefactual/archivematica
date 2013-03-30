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
# @subpackage FPRClient
# @author Joseph Perry <joseph@artefactual.com>

import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface

def removeLinks():
    sql = "SET foreign_key_checks = 0;"
    databaseInterface.runSQL(sql)
    sql = """DELETE MicroServiceChainLinks, TasksConfigs, MicroServiceChainLinksExitCodes
FROM TasksConfigs
INNER JOIN MicroServiceChainLinks ON MicroServiceChainLinks.currentTask = TasksConfigs.pk
INNER JOIN MicroServiceChainLinksExitCodes ON MicroServiceChainLinks.pk = MicroServiceChainLinksExitCodes.microServiceChainLink
WHERE TasksConfigs.taskType = '5e70152a-9c5b-4c17-b823-c9298c546eeb' 
AND MicroServiceChainLinks.pk NOT IN (SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications); """
    databaseInterface.runSQL(sql)
    sql = "SET foreign_key_checks = 1;"
    databaseInterface.runSQL(sql)

if __name__ == '__main__':
    removeLinks()