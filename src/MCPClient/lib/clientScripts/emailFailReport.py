#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
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

from __future__ import print_function

import argparse
from lxml import etree
import sys

import django
from django.conf import settings as mcpclient_settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import connection

from main.models import Job, Report

from custom_handlers import get_script_logger
from externals.HTML import HTML

from lib.job_email_report import run_report


django.setup()

logger = get_script_logger('archivematica.mcp.client.emailFailReport')

COLORS = {
    Job.STATUS_COMPLETED_SUCCESSFULLY: '#dff0d8',
    Job.STATUS_FAILED: '#f2dede',
    'default': 'yellow',
}


def get_emails_from_dashboard_users():
    return User.objects.filter(is_active=True).values_list('email', flat=True).exclude(email__in=['demo@example.com', ''])


def send_email(subject, to, content):
    try:
        logger.info('Sending email...')
        return send_mail(
            subject=subject,
            message='Please see the attached HTML document',
            from_email=mcpclient_settings.DEFAULT_FROM_EMAIL,
            recipient_list=to,
            html_message=content,
        )
    except:
        logger.exception('Report email was not delivered')
        raise
    else:
        logger.info('Report sent successfully!')


def get_file_stats(cursor, unit_type, unit_uuid):
    sql = """
        SELECT
            COUNT(fileUUID)                        AS 'Number of files',
            sum(fileSize)                          AS 'Total file size',
            sum(fileSize)/count(fileUUID)/1000     AS 'Average file size KB',
            sum(fileSize)/count(fileUUID)/1000000  AS 'Average file size MB'
        FROM Files
    """
    if unit_type == 'sip':
        sql += ' WHERE sipUUID = %s;'
    elif unit_type == 'transfer':
        sql += ' WHERE transferUUID = %s;'
    cursor.execute(sql, [unit_uuid])
    return cursor.fetchone()


def get_processing_time(cursor, unit_type, unit_uuid):
    sql = """
        SELECT SEC_TO_TIME(SUM(TIMESTAMPDIFF(SECOND, Tasks.startTime, Tasks.endTime)))
        FROM Tasks
        LEFT JOIN Jobs ON Tasks.jobUUID = Jobs.jobUUID
        WHERE Jobs.SIPUUID = %s
    """
    if unit_type == 'sip':
        sql += ' AND Jobs.unitType IN ("unitSIP", "unitDIP");'
    elif unit_type == 'transfer':
        sql += ' AND Jobs.unitType IN ("unitTransfer");'
    cursor.execute(sql, [unit_uuid])
    return cursor.fetchone()


def get_unit_statistical_data_html(unit_type, unit_uuid):
    fields = [
        'Unit type',
        'Total time processing',
        'Total file size',
        'Number of files',
        'Average file size KB',
        'Average file size MB',
    ]
    values = (unit_type,)
    unit_type = unit_type.lower()
    if unit_type not in ('sip', 'transfer'):
        raise ValueError('Unexpected value in unit_type: {}'.format(unit_type))
    with connection.cursor() as cursor:
        values += get_processing_time(cursor, unit_type, unit_uuid)
        values += get_file_stats(cursor, unit_type, unit_uuid)
    return HTML.table([values], header_row=fields)


def get_unit_job_log_html(sip_uuid):
    """
    Generate a string containing a HTML table with the jobs of a given unit
    identifier.
    """
    parser = etree.HTMLParser(remove_blank_text=True)
    rows = Job.objects.filter(sipuuid=sip_uuid, subjobof='').exclude(jobtype='Email fail report').order_by('-createdtime', '-createdtimedec').values_list('jobtype', 'currentstep', 'createdtime')
    html = HTML.table(rows, header_row=['Type', 'Status', 'Started'])
    table = etree.fromstring(html, parser).find('body/table')
    default_bgcolor = COLORS.get('default')

    i = 0
    for tr in table.findall('tr'):
        # Ignore header
        if i == 0:
            i += 1
            continue

        status = rows[i - 1][1]
        bgcolor = COLORS.get(status, default_bgcolor)
        tr.set('bgcolor', bgcolor)
        i += 1

    return etree.tostring(table)


def get_content_for(unit_type, unit_name, unit_uuid, html=True):
    logger.info('Generating report content (unit_type=%s, unit_uuid=%s, html=%s)', unit_type, unit_uuid, html)
    if html:
        root = etree.Element('HTML')
        body = etree.SubElement(root, 'BODY')
    else:
        root = etree.Element('DIV')

    parser = etree.HTMLParser(remove_blank_text=True)

    try:
        htmlcode1 = get_unit_statistical_data_html(unit_type, unit_uuid)
        t1 = etree.fromstring(htmlcode1, parser).find('body/table')

        if html:
            body.append(t1)
            etree.SubElement(body, 'p')
        else:
            root.append(t1)
            etree.SubElement(root, 'p')
    except:
        pass

    html2code = get_unit_job_log_html(unit_uuid)
    t2 = etree.fromstring(html2code, parser).find('body/table')

    if html:
        body.append(t2)
    else:
        root.append(t2)

    return etree.tostring(root, pretty_print=True)


def store_report(content, unit_type, unit_name, unit_uuid):
    logger.info('Storing report in database (unit_type=%s, unit_uuid=%s)', unit_type, unit_uuid)
    Report.objects.create(content=content, unittype=unit_type, unitname=unit_name, unitidentifier=unit_uuid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--unitType', action='store', dest='unit_type', required=True)
    parser.add_argument('-i', '--unitIdentifier', action='store', dest='unit_uuid', required=True)
    parser.add_argument('-n', '--unitName', action='store', dest='unit_name', default='')
    parser.add_argument('-f', '--from', action='store', dest='from', default='ArchivematicaSystem@archivematica.org')
    parser.add_argument('--stdout', action='store_true', dest='stdout', default=False)
    args = parser.parse_args()

    to = get_emails_from_dashboard_users()
    if not to:
        logger.error('Nobody to send it to. Please add users with valid email addresses in the dashboard.')
        sys.exit(1)
    subject = 'Archivematica Fail Report for %s: %s-%s' % (args.unit_type, args.unit_name, args.unit_uuid)

    # Generate report in HTML and send it by email
    content = get_content_for(args.unit_type, args.unit_name, args.unit_uuid, html=True)
    send_email(subject, to, content)

    if args.stdout:
        print(content)

    # Generate report in plain text and store it in the database
    content = get_content_for(args.unit_type, args.unit_name, args.unit_uuid, html=False)
    store_report(content, args.unit_type, args.unit_name, args.unit_uuid)

    run_report(args.unit_uuid)
