#!/usr/bin/python -OO
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
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>

import os
import sys
import lxml.etree as etree

# dashboard
from main.models import File

import archivematicaXMLNamesSpace as ns
# archivematicaCommon
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
    mdRef = etree.Element(ns.metsBNS + "mdRef")
    mdRef.set("LABEL", LABEL)
    mdRef.set(ns.xlinkBNS +"href", directoryPathSTR)
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
        # Find the mets file. May find none.
        path = "%SIPDirectory%{}/mets.xml".format(os.path.dirname(filePath))
        try:
            mets = File.objects.get(currentlocation=path, transfer_id=transferUUID)
        except File.DoesNotExist:
            pass
        else:
            metsFileUUID = mets.uuid
            metsLoc = mets.currentlocation.replace("%SIPDirectory%", "", 1)
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

            path = "%SIPDirectory%{}/mets.xml".format(fullDir2)
            try:
                f = File.objects.get(currentlocation=path, transfer_id=transferUUID)
            except File.DoesNotExist:
                pass
            else:
                metsFileUUID = f.uuid
                metsLoc = f.currentlocation.replace("%SIPDirectory%", "", 1)
                metsLocation = os.path.join(fullDir, "mets.xml")
                print metsLocation
                LABEL = "mets.xml-" + metsFileUUID
                ret.append(createMDRefDMDSec(LABEL, metsLocation, metsLoc))

    except Exception as inst:
        print >>sys.stderr, "Error creating mets dspace mdref", fileUUID, filePath
        print >>sys.stderr, type(inst), inst.args
        sharedVariablesAcrossModules.globalErrorCount +=1

    return ret
