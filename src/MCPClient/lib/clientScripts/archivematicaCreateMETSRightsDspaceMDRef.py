#!/usr/bin/python -OO
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

from archivematicaXMLNamesSpace import *
import os
import sys
import lxml.etree as etree
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from sharedVariablesAcrossModules import sharedVariablesAcrossModules


def createMDRefDMDSec(LABEL, itemdirectoryPath, directoryPathSTR):
    XPTR = "xpointer(id("
    tree = etree.parse(itemdirectoryPath)
    root = tree.getroot()
    a = """<amdSec ID="amd_496">
<rightsMD ID="rightsMD_499">"""
    for item in root.findall("{http://www.loc.gov/METS/}amdSec/{http://www.loc.gov/METS/}rightsMD"):
        #print "rights id:", item.get("ID")
        XPTR = "%s %s" % (XPTR, item.get("ID"))
    XPTR = XPTR.replace(" ", "'", 1) + "'))"
    mdRef = etree.Element("mdRef")
    mdRef.set("LABEL", LABEL)
    mdRef.set(xlinkBNS +"href", directoryPathSTR)
    mdRef.set("MDTYPE", "OTHER")
    mdRef.set("OTHERMDTYPE", "METSRIGHTS")
    mdRef.set("LOCTYPE","OTHER")
    mdRef.set("OTHERLOCTYPE", "SYSTEM")
    mdRef.set("XPTR", XPTR)
    return mdRef



def archivematicaCreateMETSRightsDspaceMDRef(fileUUID, filePath, transferUUID, itemdirectoryPath):
    ret = []
    try:
        print fileUUID, filePath
        #find the mets file
        sql = "SELECT fileUUID, currentLocation FROM Files WHERE currentLocation = '%%SIPDirectory%%%s/mets.xml' AND transferUUID = '%s';" % (os.path.dirname(filePath), transferUUID)
        rows = databaseInterface.queryAllSQL(sql)
        for row in rows:
            metsFileUUID = row[0]
            metsLoc = row[1].replace("%SIPDirectory%", "", 1)
            metsLocation = os.path.join(os.path.dirname(itemdirectoryPath), "mets.xml")
            LABEL = "mets.xml-%s" % (metsFileUUID)
            ret.append(createMDRefDMDSec(LABEL, metsLocation, metsLoc))

        base = os.path.dirname(os.path.dirname(itemdirectoryPath))
        base2 = os.path.dirname(os.path.dirname(filePath))

        for dir in os.listdir(base):
            fullDir = os.path.join(base, dir)
            fullDir2 = os.path.join(base2, dir)
            print fullDir
            if dir.startswith("ITEM"):
                print "continue"
                continue
            if not os.path.isdir(fullDir):
                continue
            sql = "SELECT fileUUID, currentLocation FROM Files WHERE currentLocation = '%%SIPDirectory%%%s/mets.xml' AND transferUUID = '%s';" % (fullDir2, transferUUID)
            print sql
            rows = databaseInterface.queryAllSQL(sql)
            for row in rows:
                print row
                metsFileUUID = row[0]
                metsLoc = row[1].replace("%SIPDirectory%", "", 1)
                metsLocation = os.path.join(fullDir, "mets.xml")
                print metsLocation
                LABEL = "mets.xml-%s" % (metsFileUUID)
                ret.append(createMDRefDMDSec(LABEL, metsLocation, metsLoc))




    except Exception as inst:
        print >>sys.stderr, "Error creating mets dspace mdref", fileUUID, filePath
        print >>sys.stderr, type(inst), inst.args
        sharedVariablesAcrossModules.globalErrorCount +=1

    return ret
