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
import uuid
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
#databaseInterface.printSQL = True

def addLinks():
    #Find all command relationships without links.
    CommandClassifications = {"3141bc6f-7f77-4809-9244-116b235e7330":"Normalize access",
     "3d1b570f-f500-4b3c-bbbc-4c58aad05c27":"Normalize preservation",
     "27c2969b-b6a0-441d-888d-85292b692064":"Normalize thumbnail",
     "5934dd0b-9f7c-4091-8607-47f519f5c095":"Skipable"}
    
    sql = "SELECT CommandRelationships.pk, commandClassification FROM CommandRelationships WHERE CommandRelationships.pk NOT IN (SELECT taskTypePKReference FROM TasksConfigs WHERE taskType = '5e70152a-9c5b-4c17-b823-c9298c546eeb');"
    rows = databaseInterface.queryAllSQL(sql)
    for cr, cc in rows:
        if cc not in CommandClassifications:
            print >>sys.stderr, "Invalid Command Classification (%s) for Command Relationship: %s" % (cc, cr)
        #create new taskConfig
        taskConfigPK = uuid.uuid4().__str__() 
        taskConfigDescription = CommandClassifications[cc]
        if taskConfigDescription == "Skipable":
            continue
        
        sql = """INSERT INTO TasksConfigs SET pk='%s', 
        taskType='5e70152a-9c5b-4c17-b823-c9298c546eeb',
        taskTypePKReference='%s',
        description='%s'""" % (taskConfigPK, cr, taskConfigDescription)
        databaseInterface.runSQL(sql)
        
        
        #create new link
        linkPK = uuid.uuid4().__str__() 
        ##find default
        sql = """SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications WHERE forClassification = '%s';""" % (cc)
        rows2 = databaseInterface.queryAllSQL(sql)
        if not rows2:
            linkDefaultNextLink = "NULL"
        else:
            linkDefaultNextLink = "'%s'" % (rows2[0][0])
        
        sql = """INSERT INTO MicroServiceChainLinks SET pk = '%s',
        currentTask='%s',
        defaultNextChainLink = %s,
        microserviceGroup='Normalize';""" % (linkPK, taskConfigPK, linkDefaultNextLink)
        databaseInterface.runSQL(sql)
        
        #Create Exit Code
        exitCodesPK = uuid.uuid4().__str__()
        sql = """INSERT INTO MicroServiceChainLinksExitCodes SET pk = '%s',
        microServiceChainLink = '%s',
        exitCode = 0,
        nextMicroServiceChainLink = NULL;""" % (exitCodesPK, linkPK)
        databaseInterface.runSQL(sql)

if __name__ == '__main__':
    addLinks()
    