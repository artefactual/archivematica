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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from optparse import OptionParser
from lxml import etree

# dashboard
from django.contrib.auth.models import User

# archivematicaCommon
import databaseInterface
from externals.HTML import HTML 

def getEmailsFromDashboardUsers():
    return [u[0] for u in User.objects.filter(is_active=True).values_list('email').exclude(email__in=['demo@example.com', ''])]


def sendEmail(subject, to, from_, content, server):
    to2 = ", ".join(to) 
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to2
    
    part1 = MIMEText(content, 'html')
    part2 = MIMEText("This email requires rendering of html to view", 'plain')
    
    msg.attach(part1)
    #msg.attach(part2)
    
    server = smtplib.SMTP(server)
    server.sendmail(from_, to, msg.as_string())
    server.quit()

def getUnitStatisticalDataHTML(unitIdentifier):
    fields = ["unitType", "Total time processing", "total file size", "number of files", "average file size KB", "average file size MB"]
    sql = """SELECT `{fields}` FROM PDI_by_unit WHERE SIP_OR_TRANSFER_UUID = %s;""".format(fields="`, `".join(fields))
    rows = databaseInterface.queryAllSQL(sql, (unitIdentifier,))
    return HTML.table(rows, header_row=fields)

def getUnitJobLogHTML(unitIdentifier):
    parser = etree.HTMLParser(remove_blank_text=True)

    sql = """SELECT Jobs.jobType, Jobs.currentStep, Jobs.createdTime, jobUUID
    FROM Jobs 
    WHERE Jobs.SIPUUID = %s
    AND Jobs.jobType != 'Email fail report'
    AND subJobOf = ''
    ORDER BY Jobs.createdTime DESC, Jobs.createdTimeDec DESC;"""
    
    rows2Temp = databaseInterface.queryAllSQL(sql, (unitIdentifier,))

    rows2=[]
    for row in rows2Temp:
        newRow = []
        newRow.append(row[0])
        newRow.append(row[1])
        newRow.append(row[2])

        # TODO: Fix issues with duration
        if False:
            try:
                databaseInterface.printErrors = False
                sql = """SELECT SEC_TO_TIME(jobDurationsView.time_from_job_created_till_end_of_processing_in_seconds) FROM  jobDurationsView WHERE jobUUID = %s;"""
                duration = databaseInterface.queryAllSQL(sql, (row[3],))
                if duration and duration[0] and duration[0][0]:
                    newRow.append(duration[0][0])
                else:
                    newRow.append("-")
                databaseInterface.printErrors = True
            except:
                databaseInterface.printErrors = True
                duration = 0
                newRow.append(0)

        rows2.append(newRow)

    htmlcode2 = HTML.table(rows2, header_row=["Type", "Status", "Started"]) # TODO: Re-add duration
    t2 = etree.fromstring(htmlcode2, parser).find("body/table")
    i = 0  
    for tr in t2.findall("tr"):
        #header row
        if i == 0:
            i+=1
            #tr.set("bgcolor", "#00FF00")
            continue
        
        #job row
        status = rows2[i-1][1]
        if status == "Completed successfully":
            tr.set("bgcolor", "#dff0d8")
        elif status == "Failed":
            tr.set("bgcolor", "#f2dede")
        else:
            tr.set("bgcolor", "yellow")
        i+=1

    return etree.tostring(t2)

def getContentFor(unitType, unitName, unitIdentifier, as_html_page=True):
    if as_html_page:
        root = etree.Element("HTML")
        body = etree.SubElement(root, "BODY")
    else:
        root = etree.Element("DIV")

    parser = etree.HTMLParser(remove_blank_text=True)
    
    try:
        htmlcode1 = getUnitStatisticalDataHTML(unitIdentifier)
        t1 = etree.fromstring(htmlcode1, parser).find("body/table")  

        if as_html_page:
            body.append(t1)
            etree.SubElement(body, "p")
        else:
            root.append(t1)
            etree.SubElement(root, "p")
    except:
        pass

    html2code = getUnitJobLogHTML(unitIdentifier)
    t2 = etree.fromstring(html2code, parser).find("body/table")

    if as_html_page:
        body.append(t2)
    else:
        root.append(t2)

    return etree.tostring(root, pretty_print=True)

def storeReport(content, type, name, UUID):
    sql = """INSERT INTO Reports (content, unitType, unitName, unitIdentifier) VALUES (%s, %s, %s, %s)"""
    databaseInterface.queryAllSQL(sql, (content, type, name, UUID))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-t",  "--unitType",          action="store", dest="unitType", default="")
    parser.add_option("-i",  "--unitIdentifier",    action="store", dest="unitIdentifier", default="")
    parser.add_option("-n",  "--unitName",    action="store", dest="unitName", default="")
    parser.add_option("-d",  "--date",     action="store", dest="eventDateTime", default="")
    parser.add_option("-s",  "--server",     action="store", dest="server", default="")

    (opts, args) = parser.parse_args()
    
    to = getEmailsFromDashboardUsers()
    if not to:
        print "Nobody to send it to. Please add users with valid email addresses in the dashboard."
        exit(1)
    subject = "Archivematica Fail Report for %s: %s-%s" % (opts.unitType, opts.unitName, opts.unitIdentifier)
    from_ = "ArchivematicaSystem@archivematica.org"
    content = getContentFor(opts.unitType, opts.unitName, opts.unitIdentifier)
    server = "localhost"
    
    sendEmail(subject, to, from_, content, server)

    content = getContentFor(opts.unitType, opts.unitName, opts.unitIdentifier, False)
    storeReport(content, opts.unitType, opts.unitName, opts.unitIdentifier)
