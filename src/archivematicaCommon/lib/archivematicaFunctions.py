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
# @subpackage archivematicaCommon
# @author Joseph Perry <joseph@artefactual.com>
# @version svn: $Id$

import lxml.etree as etree
import os
import sys

def unicodeToStr(string):
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string

def strToUnicode(string):
    if isinstance(string, str):
        string = string.decode("utf-8")
    return string


def getTagged(root, tag):
    ret = []
    for element in root:
        #print element.tag
        #print tag
        #print element.tag == tag
        if element.tag == tag:
            ret.append(element)
            #return ret #only return the first encounter
    return ret


def appendEventToFile(SIPLogsDirectory, fileUUID, eventXML):
    xmlFile = SIPLogsDirectory + "fileMeta/" + fileUUID + ".xml"
    appendEventToFile2(xmlFile, eventXML)

def appendEventToFile2(xmlFile, eventXML):
    tree = etree.parse( xmlFile )
    root = tree.getroot()

    events = getTagged(root, "events")[0]
    events.append(eventXML)

    tree = etree.ElementTree(root)
    tree.write(xmlFile)

def archivematicaRenameFile(SIPLogsDirectory, fileUUID, newName, eventXML):
    xmlFile = SIPLogsDirectory + "fileMeta/" + fileUUID + ".xml"
    newName = newName.decode('utf-8')
    tree = etree.parse( xmlFile )
    root = tree.getroot()
    xmlFileName = getTagged(root, "currentFileName")[0]
    xmlFileName.text = newName

    events = getTagged(root, "events")[0]
    events.append(eventXML)

    #print etree.tostring(root, pretty_print=True)

    tree = etree.ElementTree(root)
    tree.write(xmlFile)


def fileNoLongerExists(root, objectsDir):
    """Returns 0 if not deleted, 1 if deleted, -1 if deleted, but already an event to indicated it has been removed"""
    events = getTagged(root, "events")[0]

    for event in getTagged(events, "event"):
        #print >>sys.stderr , "event"
        etype = getTagged(event, "eventType")
        if len(etype) and etype[0].text == "fileRemoved":
            #print >>sys.stderr , "file already removed"
            return -1

    currentName = getTagged(root, "currentFileName")[0].text

    currentName2 = currentName.replace("objects", objectsDir, 1)
    if os.path.isfile(currentName2.encode('utf8')):
        return 0
    else:
        print currentName
        return 1

def escapeForCommand(string):
    ret = string
    if isinstance(ret, unicode) or isinstance(ret,str) :
        ret = ret.replace("\\", "\\\\")
        ret = ret.replace("\"", "\\\"")
        #ret = ret.replace("'", "\\'")
        ret = ret.replace("$", "\\$")
    return ret

def escape(string):
    #string = string.decode('utf-8')
    return string
