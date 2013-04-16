#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage Dashboard
# @author Joseph Perry <joseph@artefactual.com>
# @autho Justin Simpson <jsimpson@artefactual.com>
#import sys
#sys.path.append("/usr/lib/archivematica/archivematicaCommon")

#import databaseInterface
#databaseInterface.printSQL = True
from components import helpers
from django.db import connection
    
def getNormalizationReportQuery(sipUUID, idsRestriction=""):
    if idsRestriction:
        idsRestriction = 'AND (%s)' % idsRestriction  
    
    cursor = connection.cursor()
        
    sql =  """
    SELECT variableValue 
    FROM UnitVariables 
    WHERE unitType = 'SIP' 
    AND variable = 'normalizationFileIdentificationToolIdentifierTypes' 
    AND unitUUID = '{0}';
    """.format(sipUUID)
    
    cursor.execute(sql)
    
    fileIDTypeUsed = cursor.fetchone()
    fileIDTypeUsed = str(fileIDTypeUsed[0])
    print "fileIDTypeUsed " + fileIDTypeUsed
    sql = """
    select
        CONCAT(a.currentLocation, ' ', a.fileUUID,' ', IFNULL(b.fileID, "")) AS 'pagingIndex', 
        a.fileUUID, 
        a.location,
        substring(a.currentLocation,23) as fileName, 
        a.fileID, 
        a.description, 
        a.already_in_access_format, 
        a.already_in_preservation_format,
        b.access_normalization_attempted,
        b.preservation_normalization_attempted,
        b.access_normalization_task_uuid,
        b.preservation_normalization_task_uuid,
        b.access_normalization_failed,
        b.access_task_exitCode,
        b.preservation_task_exitCode
    from
        (select
            f.fileUUID,
            f.sipUUID, 
            f.originalLocation as location,
            f.currentLocation, 
            fid.pk as 'fileID',
            fid.description, 
            fid.validAccessFormat AS 'already_in_access_format', 
            fid.validPreservationFormat AS 'already_in_preservation_format'
        from 
        Files f
        Join
        FilesIdentifiedIDs fii on f.fileUUID = fii.fileUUID
        Join
        FileIDs fid on fii.fileID = fid.pk 
        Join
        FileIDTypes on FileIDTypes.pk = fid.fileIDType
        where 
            f.fileGrpUse in ('original', 'service')
            and f.sipUUID = '{0}'
            and {1}
        ) a 
    Left Join
        (select
            cr.fileID,
            j.sipUUID,
            max(if(cc.classification = 'access', t.taskUUID, null)) IS NOT NULL as access_normalization_attempted,
            max(if(cc.classification = 'preservation', t.taskUUID, null)) IS NOT NULL as preservation_normalization_attempted,
            max(if(cc.classification = 'access', t.taskUUID, null)) as access_normalization_task_uuid,
            max(if(cc.classification = 'preservation', t.taskUUID, null)) as preservation_normalization_task_uuid,
            max(if(cc.classification = 'access', t.exitCode, null)) != 0 AS access_normalization_failed,
            max(if(cc.classification = 'preservation', t.exitCode, null)) != 0 AS preservation_normalization_failed,
            max(if(cc.classification = 'access', t.exitCode, null)) as access_task_exitCode,
            max(if(cc.classification = 'preservation', t.exitCode, null)) as preservation_task_exitCode
        from 
            CommandRelationships cr
            Join
            CommandClassifications cc on cr.commandClassification  = cc.pk
            Join 
            TasksConfigs tc on tc.taskTypePKReference = cr.pk
            join
            MicroServiceChainLinks ml on tc.pk = ml.currentTask
            Join
            Jobs j on j.MicroServiceChainLinksPK = ml.pk 
            join
            Tasks t on t.jobUUID = j.jobUUID
        where 
            cc.classification in ('preservation', 'access')
        group by cr.fileID
        ) b
    on a.fileID = b.fileID and a.sipUUID = b.sipUUID;
    """.format(sipUUID, fileIDTypeUsed)
    
    cursor.execute(sql)
    objects = helpers.dictfetchall(cursor)
    #objects = databaseInterface.queryAllSQL(sql)
    return objects 
    

if __name__ == '__main__':
    import sys
    uuid = "'%s'" % (sys.argv[1])
    sys.path.append("/usr/lib/archivematica/archivematicaCommon")
    #import databaseInterface
    #databaseInterface.printSQL = True
    print "testing normalization report"
    sql = getNormalizationReportQuery(sipUUID=uuid)
    print sql
    #rows = databaseInterface.queryAllSQL(sql)
    #for row in rows:
    #    print row
    #    print
