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
#import sys
#sys.path.append("/usr/lib/archivematica/archivematicaCommon")

    
def getNormalizationReportQuery(idsRestriction=""):
    if idsRestriction:
        idsRestriction = 'AND (%s)' % idsRestriction  
    return """
    SELECT CONCAT(Files.currentLocation, ' ', Files.fileUUID,' ', IFNULL(q_1.fileID, "")) AS 'pagingIndex', Files.currentLocation AS 'fileName', q_1.description , q_1.*
    FROM
        Files
    LEFT OUTER JOIN
        (select
            f.fileUUID, f.currentLocation , fid.pk AS 'fileID', fid.description, fid.validAccessFormat AS 'already_in_access_format', fid.validPreservationFormat AS 'already_in_preservation_format',
            max(if(cc.classification = 'access', t.taskUUID, null)) IS NOT NULL as access_normalization_attempted,
            max(if(cc.classification = 'preservation', t.taskUUID, null)) IS NOT NULL as preservation_normalization_attempted,
            max(if(cc.classification = 'access', t.taskUUID, null)) as access_normalization_task_uuid,
            max(if(cc.classification = 'preservation', t.taskUUID, null)) as preservation_normalization_task_uuid,
            max(if(cc.classification = 'access', t.exitCode, null)) != 0 AS access_normalization_failed,
            max(if(cc.classification = 'preservation', t.exitCode, null)) != 0 AS preservation_normalization_failed,
            max(if(cc.classification = 'access', t.exitCode, null)) as access_task_exitCode,
            max(if(cc.classification = 'preservation', t.exitCode, null)) as preservation_task_exitCode
        from
            Files f
            Join
            FilesIdentifiedIDs fii on f.fileUUID = fii.fileUUID
            Join
            FileIDs fid on fii.fileID = fid.pk 
            Join
            CommandRelationships cr on cr.fileID = fid.pk
            Join
            CommandClassifications cc on cr.commandClassification  = cc.pk
            join
            TasksConfigs tc on tc.taskTypePKReference = cr.pk
            join
            MicroServiceChainLinks ml on tc.pk = ml.currentTask
            join
            Jobs j on j.MicroServiceChainLinksPK = ml.pk and j.sipUUID = f.sipUUID
            join
            Tasks t on t.jobUUID = j.jobUUID
            join
            FileIDTypes on FileIDTypes.pk = fid.fileIDType 
        where
            f.sipUUId = %s and f.fileGrpUse in ('original', 'service')
            and cc.classification in ('preservation', 'access')
            AND ml.pk NOT IN (SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications)
            """ + idsRestriction + """
        group by
            fileUUID, fid.pk) AS q_1
    ON Files.fileUUID = q_1.fileUUID
    WHERE Files.sipUUId = %s
    AND fileGrpUse IN ('original', 'service') ;"""



if __name__ == '__main__':
    import sys
    uuid = "'%s'" % (sys.argv[1])
    sys.path.append("/usr/lib/archivematica/archivematicaCommon")
    import databaseInterface
    #databaseInterface.printSQL = True
    print "testing normalization report"
    sql = getNormalizationReportQuery()
    sql = sql % (uuid, uuid)
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        print row
        print
