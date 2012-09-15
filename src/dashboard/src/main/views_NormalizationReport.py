#!/usr/bin/python -OO
# -*- coding: utf-8 -*-
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.    If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage Dashboard
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

def getNormalizationReportQuery():
    return """
SELECT

        Tasks.fileUUID AS U,
        Tasks.fileName,

        (SELECT IF(Tasks.taskUUID IS NULL, '', Tasks.taskUUID)
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Jobs.jobType = 'Normalize access' AND
            Tasks.fileUUID = U
        ) AS 'access_normalization_task_uuid',

        (SELECT IF(Tasks.taskUUID IS NULL, '', Tasks.taskUUID)
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Jobs.jobType = 'Normalize preservation' AND
            Tasks.fileUUID = U
        ) AS 'preservation_normalization_task_uuid',

        Tasks.fileUUID IN (
          SELECT Tasks.fileUUID
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Jobs.jobType = 'Normalize preservation' AND
            Jobs.MicroServiceChainLinksPK NOT IN (SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications ) AND
            Tasks.stdOut LIKE '%%[Command]%%')
        AS 'preservation_normalization_attempted',

        (
          SELECT Tasks.exitCode
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Jobs.jobType = 'Normalize preservation' AND
            Tasks.fileUUID = U
        ) != 0
        AS 'preservation_normalization_failed',

       filesPreservationAccessFormatStatus.inPreservationFormat AS 'already_in_preservation_format',

        Tasks.fileUUID NOT IN (
          SELECT Tasks.fileUUID
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Tasks.exec = 'transcoderNormalizeAccess_v0.0' AND
            Tasks.stdOut LIKE '%%description: Copying File.%%') AND
            Tasks.fileUUID IN (
              SELECT Tasks.fileUUID
              FROM Tasks
              JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
              WHERE
                Jobs.SIPUUID = %s AND
                Jobs.jobType = 'Normalize access' AND
                Tasks.stdOut LIKE '%%[Command]%%' AND
                Jobs.MicroServiceChainLinksPK NOT IN (SELECT MicroserviceChainLink FROM DefaultCommandsForClassifications ) AND
                Tasks.stdOut NOT LIKE '%%Not including %% in DIP.%%'  )
        AS 'access_normalization_attempted',

        (
          SELECT Tasks.exitCode
          FROM Tasks
          JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
          WHERE
            Jobs.SIPUUID = %s AND
            Jobs.jobType = 'Normalize access' AND
            Tasks.fileUUID = U
        ) != 0
        AS 'access_normalization_failed',

        filesPreservationAccessFormatStatus.inAccessFormat AS 'already_in_access_format',

        (
          SELECT Files.originalLocation
          FROM Files
          WHERE
            Files.fileUUID = U
        )
        AS 'location',

        Tasks.jobUUID AS 'jobUUID'

      FROM Files
      LEFT OUTER JOIN Tasks ON Files.fileUUID = Tasks.fileUUID
      LEFT OUTER JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
      LEFT OUTER JOIN filesPreservationAccessFormatStatus ON filesPreservationAccessFormatStatus.fileUUID = Files.fileUUID
      WHERE
        Jobs.SIPUUID = %s AND
        Files.fileGrpUse != 'preservation' AND
        Files.currentLocation LIKE '\%%SIPDirectory\%%objects/%%'
      GROUP BY Tasks.fileUUID
      ORDER BY Tasks.fileName;
"""

if __name__ == '__main__':
    import sys
    uuid = "'%s'" % (sys.argv[1])
    sys.path.append("/usr/lib/archivematica/archivematicaCommon")
    import databaseInterface
    print "testing normalization report"
    sql = getNormalizationReportQuery()
    sql = sql % ( uuid, uuid, uuid, uuid, uuid, uuid, uuid, uuid )
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        print row
        print
