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
# @subpackage transcoder
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import uuid
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
import traceback
import lxml.etree as etree
from optparse import OptionParser

databaseInterface.printSQL = True


if __name__ == '__main__':
    sql = """SELECT CommandRelationships.pk, CommandClassifications.classification, TasksConfigs.pk FROM CommandRelationships JOIN CommandClassifications ON CommandRelationships.commandClassification = CommandClassifications.pk LEFT OUTER JOIN TasksConfigs ON TasksConfigs.taskTypePKReference = CommandRelationships.pk;"""
    rows = databaseInterface.queryAllSQL(sql) 
    for row in rows:
        CommandRelationship, classification, TasksConfig = row
        defualtPreservationNextChainLink = "NULL"
        defaultAccessNextChainLink = "'197e9671-0b98-4a4a-81de-46c835a3accd'"
        defaultThumbnailNextChainLink = "'e8b0a95e-2ac6-49a7-bb9e-308ea0567651'"
        if TasksConfig == None:
            if classification not in ["access", "preservation", "thumbnail"]:
                continue
            description = "Normalize %s" % (classification)
            TasksConfig = uuid.uuid4().__str__()
            
            databaseInterface.runSQL("""Insert INTO TasksConfigs (pk, taskType, taskTypePKReference, description)
                VALUES ('%s', '5e70152a-9c5b-4c17-b823-c9298c546eeb', '%s', '%s');""" % (TasksConfig, CommandRelationship, description) )
            
            defaultNextChainLink = "NULL"
            if classification == ["access"]:
                defaultNextChainLink = defaultAccessNextChainLink
            elif classification == ["thumbnail"]:
                defaultNextChainLink = defaultThumbnailNextChainLink
            MicroServiceChainLink = uuid.uuid4().__str__()
            databaseInterface.runSQL("""Insert INTO MicroServiceChainLinks (pk, currentTask, defaultNextChainLink, microserviceGroup )
                VALUES ('%s', '%s', %s, 'Normalize');""" % (MicroServiceChainLink, TasksConfig, defaultNextChainLink ) )
            
            MicroServiceChainLinksExitCode = uuid.uuid4().__str__()
            databaseInterface.runSQL("""Insert INTO MicroServiceChainLinksExitCodes (pk, microServiceChainLink)
                VALUES ('%s', '%s');""" % (MicroServiceChainLinksExitCode, MicroServiceChainLink) )