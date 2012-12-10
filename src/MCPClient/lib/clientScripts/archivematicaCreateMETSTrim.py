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




def getTrimDmdSec(baseDirectoryPath, fileGroupIdentifier):
    #containerMetadata
    ret = etree.Element("dmdSec") 
    mdWrap = etree.SubElement(ret, "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = etree.SubElement(mdWrap, "xmlData")
    
    dublincore = etree.SubElement(xmlData, "dublincore", attrib=None, nsmap={None:dctermsNS})
    tree = etree.parse(os.path.join(baseDirectoryPath, "objects", "ContainerMetadata.xml"))
    root = tree.getroot()
    
    
    etree.SubElement(dublincore, dctermsBNS + "title").text = root.find("Container/TitleFreeTextPart").text
    etree.SubElement(dublincore, dctermsBNS + "creator").text = root.find("Container/Department").text
    etree.SubElement(dublincore, dctermsBNS + "provenance").text = root.find("Container/OPR").text
    etree.SubElement(dublincore, dctermsBNS + "identifier").text = root.find("Container/RecordNumber").text.split('/')[-1]
    
    
     
    
    #get objects count
    sql = "SELECT fileUUID FROM Files WHERE removedTime = 0 AND %s = '%s' AND fileGrpUse='original';" % ('sipUUID', fileGroupIdentifier)
    rows = databaseInterface.queryAllSQL(sql)
    print '%d digital objects' % (len(rows))
    
    sql = "SELECT currentLocation FROM Files WHERE removedTime = 0 AND %s = '%s' AND fileGrpUse='TRIM file metadata';" % ('sipUUID', fileGroupIdentifier)
    rows = databaseInterface.queryAllSQL(sql)
    
    minDateMod =  None
    maxDateMod =  None
    for row in rows:
        fileMetadataXmlPath = row[0].replace('%SIPDirectory%', baseDirectoryPath, 1)
        if os.path.isfile(fileMetadataXmlPath):
            tree2 = etree.parse(fileMetadataXmlPath)
            root2 = tree2.getroot()
            dateMod = root2.find("Document/DateModified").text
            if minDateMod ==  None or dateMod < minDateMod:
               minDateMod = dateMod
            if maxDateMod ==  None or dateMod > maxDateMod:
               maxDateMod = dateMod

    etree.SubElement(dublincore, dctermsBNS + "date").text = "%s/%s" % (minDateMod, maxDateMod)
    
    #print etree.tostring(dublincore, pretty_print = True)
    return ret