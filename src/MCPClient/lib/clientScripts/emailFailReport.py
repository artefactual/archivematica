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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
import smtplib
import string
from optparse import OptionParser
import sys
from lxml import etree
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from externals.HTML import HTML 


def getEmailsFromList():
    return ["joseph@artefactual.com"]

def getEmailsFromDashboardUsers():
    return []

def getEmailsFromUnitApprovingUser():
    return []


def sendEmail(subject, to, from_, content, server):
    to2 = ", ".join(to) 
    email = string.join((
            "From: %s" % from_,
            "To: %s" % to2,
            "Subject: %s" % subject ,
            "",
            content
            ), "\r\n")
    
    server = smtplib.SMTP(server)
    server.sendmail(from_, to, email)
    server.quit()




def getContentFor(unitType, unitName, unitIdentifier):
    root = etree.Element("HTML")
    body = etree.SubElement(root, "body")
    parser = etree.HTMLParser(remove_blank_text=True)
    
    
    fields = ["unitType", "Total time processing", "total file size", "number of files", "average file size KB", "average file size MB"]
    sql = """SELECT `%s` FROM PDI_by_unit WHERE SIP_OR_TRANSFER_UUID = '%s';""" % ("`, `".join(fields), unitIdentifier)
    rows = databaseInterface.queryAllSQL(sql)
    htmlcode1 = HTML.table(rows, header_row=fields)
    t1 = etree.fromstring(htmlcode1, parser).find("body/table")  
    print etree.tostring(t1)
    body.append(t1)
    
    sql = """SELECT Jobs.jobType, Jobs.currentStep, Jobs.createdTime, SEC_TO_TIME(jobDurationsView.time_from_job_created_till_end_of_processing_in_seconds)
    FROM Jobs 
    JOIN jobDurationsView ON Jobs.jobUUID = jobDurationsView.jobUUID 
    WHERE Jobs.SIPUUID = '%s' ;""" % (unitIdentifier)
    rows2 = databaseInterface.queryAllSQL(sql)
    htmlcode2 = HTML.table(rows2, header_row=["Jobs.jobType", "Jobs.currentStep", "Jobs.createdTime", "SEC_TO_TIME"])
    t2 = etree.fromstring(htmlcode2, parser).find("body/table")  
    print etree.tostring(t2)
    body.append(t2)
    
    return etree.tostring(root, pretty_print=True)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-t",  "--unitType",          action="store", dest="unitType", default="")
    parser.add_option("-i",  "--unitIdentifier",    action="store", dest="unitIdentifier", default="")
    parser.add_option("-n",  "--unitName",    action="store", dest="unitName", default="")
    parser.add_option("-d",  "--eventDateTime",     action="store", dest="eventDateTime", default="")
    parser.add_option("-s",  "--server",     action="store", dest="server", default="")

    (opts, args) = parser.parse_args()
    
    to = getEmailsFromList()
    subject = "Archivematica Fail Report for %s: %s-%s" % (opts.unitType, opts.unitName, opts.unitIdentifier)
    from_ = "ArchivematicaSystem@archivematica.org"
    content = getContentFor(opts.unitType, opts.unitName, opts.unitIdentifier)
    server = "localhost"
    
    print content
    sendEmail(subject, to, from_, content, server)