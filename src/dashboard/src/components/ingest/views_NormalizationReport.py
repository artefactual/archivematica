#!/usr/bin/env python
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
# @author Justin Simpson <jsimpson@artefactual.com>
from __future__ import absolute_import, print_function

from django.db import connection

from components import helpers


def getNormalizationReportQuery(sipUUID, idsRestriction=""):
    if idsRestriction:
        idsRestriction = "AND (%s)" % idsRestriction

    cursor = connection.cursor()

    # not fetching name of ID Tool, don't think we need it.

    sql = """
    select
        CONCAT(a.currentLocation, ' ', a.fileUUID,' ', IFNULL(a.fileID, "")) AS 'pagingIndex',
        a.fileUUID,
        a.location,
        substring(a.currentLocation,23) as fileName,
        a.fileID,
        a.description,
        a.already_in_access_format,
        a.already_in_preservation_format,
        case when c.exitCode < 2 and a.fileID is not null then 1 else 0 end as access_normalization_attempted,
        case when a.fileID is not null and c.exitcode = 1 then 1 else 0 end as access_normalization_failed,
        case when b.exitCode < 2 and a.fileID is not null then 1 else 0 end as preservation_normalization_attempted,
        case when a.fileID is not null and b.exitcode = 1 then 1 else 0 end as preservation_normalization_failed,
        c.taskUUID as access_normalization_task_uuid,
        b.taskUUID as preservation_normalization_task_uuid,
        c.exitCode as access_task_exitCode,
        b.exitCode as preservation_task_exitCode,
        d.taskUUID as preservation_derivative_validation_task_uuid,
        d.exitCode as preservation_derivative_validation_task_exitCode,
        d.stdOut as preservation_derivative_validation_task_stdOut,
        e.taskUUID as access_derivative_validation_task_uuid,
        e.exitCode as access_derivative_validation_task_exitCode,
        e.stdOut as access_derivative_validation_task_stdOut
    from (
        select
            f.fileUUID,
            f.sipUUID,
            f.originalLocation as location,
            f.currentLocation,
            fid.uuid as 'fileID',
            fid.description,
            f.fileGrpUse,
            fid.access_format AS 'already_in_access_format',
            fid.preservation_format AS 'already_in_preservation_format'
        from
            Files f
            Left Join
            FilesIdentifiedIDs fii on f.fileUUID = fii.fileUUID
            Left Join
            fpr_formatversion fid on fii.fileID = fid.uuid
        where
            f.fileGrpUse in ('original', 'service')
            and f.sipUUID = %s
        ) a
        Left Join (
        select
            j.sipUUID,
            t.fileUUID,
            t.taskUUID,
            t.exitcode
        from
            Jobs j
            Join
            Tasks t on t.jobUUID = j.jobUUID
        where
            j.jobType = 'Normalize for preservation'
        ) b
        on a.fileUUID = b.fileUUID and a.sipUUID = b.sipUUID

        Left Join (
        select
            j.sipUUID,
            t.fileUUID,
            t.taskUUID,
            t.exitcode
        from
            Jobs j
            join
            Tasks t on t.jobUUID = j.jobUUID
        Where
            j.jobType = 'Normalize for access'
        ) c
        ON a.fileUUID = c.fileUUID AND a.sipUUID = c.sipUUID

        Left Join (
        select
            j.sipUUID,
            t.fileUUID,
            t.taskUUID,
            t.exitcode,
            t.stdOut,
            dv.sourceFileUUID
        from
            Jobs j
            join
            Tasks t on t.jobUUID = j.jobUUID
            join
            Derivations dv on dv.derivedFileUUID = t.fileUUID
        Where
            j.jobType = 'Validate preservation derivatives'
        ) d
        ON a.fileUUID = d.sourceFileUUID AND a.sipUUID = d.sipUUID

        Left Join (
        select
            j.sipUUID,
            t.fileUUID,
            t.taskUUID,
            t.exitcode,
            t.stdOut,
            dv.sourceFileUUID
        from
            Jobs j
            join
            Tasks t on t.jobUUID = j.jobUUID
            join
            Derivations dv on dv.derivedFileUUID = t.fileUUID
        Where
            j.jobType = 'Validate access derivatives'
        ) e
        ON a.fileUUID = e.sourceFileUUID AND a.sipUUID = e.sipUUID

        WHERE a.sipUUID = %s
        order by (access_normalization_failed + preservation_normalization_failed) desc;
    """

    cursor.execute(sql, (sipUUID, sipUUID))
    objects = helpers.dictfetchall(cursor)
    return objects


if __name__ == "__main__":
    import sys

    uuid = "'%s'" % (sys.argv[1])
    print("testing normalization report")
    sql = getNormalizationReportQuery(sipUUID=uuid)
    print(sql)
