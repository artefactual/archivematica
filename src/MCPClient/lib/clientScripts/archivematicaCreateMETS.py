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

from archivematicaXMLNamesSpace import *

import os
import sys
import lxml.etree as etree
import MySQLdb
from xml.sax.saxutils import quoteattr
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface


UUIDsDic={}
amdSec=[]

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s",  "--basePath", action="store", dest="basePath", default="")
parser.add_option("-b",  "--basePathString", action="store", dest="basePathString", default="SIPDirectory") #transferDirectory
parser.add_option("-f",  "--fileGroupIdentifier", action="store", dest="fileGroupIdentifier", default="sipUUID") #transferUUID
parser.add_option("-S",  "--sipUUID", action="store", dest="sipUUID", default="")
parser.add_option("-x",  "--xmlFile", action="store", dest="xmlFile", default="")
parser.add_option("-a",  "--amdSec", action="store_true", dest="amdSec", default=False)
(opts, args) = parser.parse_args()
print opts


SIPUUID = opts.sipUUID
basePath = opts.basePath
XMLFile = opts.xmlFile
includeAmdSec = opts.amdSec
basePathString = "%%%s%%" % (opts.basePathString)
fileGroupIdentifier = opts.fileGroupIdentifier

def escape(string):
    string = string.decode('utf-8')
    return string


def newChild(parent, tag, text=None, tailText=None):
    child = etree.Element(tag)
    parent.append(child)
    child.text = text
    return child



#Do /SIP-UUID/
#Force only /SIP-UUID/objects
doneFirstRun = False
def createFileSec(path, parentBranch, structMapParent):
    print >>sys.stderr, "createFileSec: ", path, parentBranch, structMapParent
    doneFirstRun = True
    pathSTR = path.__str__()
    pathSTR = path.__str__()
    if pathSTR == basePath + "objects/": #IF it's it's the SIP folder, it's OBJECTS
        pathSTR = "objects"

    if path == basePath: #if it's the very first run through (recursive function)
        pathSTR = os.path.basename(os.path.dirname(basePath))

        # structMap directory
        div = newChild(structMapParent, "div")
        createFileSec(os.path.join(path, "objects/"), parentBranch, div)
        doneFirstRun = False
    filename = os.path.basename(pathSTR)

    structMapParent.set("TYPE", "directory")
    structMapParent.set("LABEL", escape(filename))


    if doneFirstRun:
        for doDirectories in [False, True]:
            print "path", type(path), path
            directoryContents = os.listdir(path)
            directoryContents.sort()
            for item in directoryContents:
                print "item", type(item), item
                itempath = os.path.join(path, item)
                if os.path.isdir(itempath):
                    if not doDirectories:
                        continue
                    # structMap directory
                    div = newChild(structMapParent, "div")

                    createFileSec(os.path.join(path, item), parentBranch, div)
                elif os.path.isfile(itempath):
                    if doDirectories:
                        continue
                    #myuuid = uuid.uuid4()
                    myuuid=""
                    #pathSTR = itempath.replace(basePath + "objects", "objects", 1)
                    pathSTR = itempath.replace(basePath, basePathString, 1)

                    print "pathSTR", type(pathSTR), pathSTR

                    sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND %s = '%s' AND Files.currentLocation = '%s';""" % (fileGroupIdentifier, SIPUUID, MySQLdb.escape_string(pathSTR))
                    c, sqlLock = databaseInterface.querySQL(sql)
                    row = c.fetchone()
                    if row == None:
                        print >>sys.stderr, "No uuid for file: \"", pathSTR, "\""
                    while row != None:
                        myuuid = row[0]
                        row = c.fetchone()
                    sqlLock.release()

                    if includeAmdSec:
                        createDigiprovMD(myuuid, itempath, myuuid)

                    pathSTR = itempath.replace(basePath, "", 1)

                    fileI = etree.SubElement( parentBranch, "file")

                    filename = ''.join(quoteattr(item).split("\"")[1:-1])
                    #filename = replace /tmp/"UUID" with /objects/

                    ID = "file-" + myuuid.__str__()
                    fileI.set("ID", escape(ID))
                    if includeAmdSec:
                        fileI.set("ADMID", "digiprov-" + item.__str__() + "-"    + myuuid.__str__())

                    Flocat = newChild(fileI, "FLocat")
                    Flocat.set(xlinkBNS + "href", escape(pathSTR) )
                    Flocat.set("LOCTYPE", "OTHER")
                    Flocat.set("OTHERLOCTYPE", "SYSTEM")

                    # structMap file
                    fptr = newChild(structMapParent, "fptr")
                    FILEID = "file-" + myuuid.__str__()
                    fptr.set("FILEID", escape(FILEID))

if __name__ == '__main__':
    root = etree.Element( "mets", \
    nsmap = {None: metsNS, "xlink": xlinkNS}, \
    attrib = { "{" + xsiNS + "}schemaLocation" : "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd" } )

    #cd /tmp/$UUID;
    opath = os.getcwd()
    os.chdir(basePath)
    path = basePath

    #if includeAmdSec:
    #    amdSec = newChild(root, "amdSec")

    fileSec = etree.Element("fileSec")
    #fileSec.tail = "\n"
    root.append(fileSec)

    sipFileGrp = etree.SubElement(fileSec, "fileGrp")
    sipFileGrp.set("USE", "original")

    structMap = newChild(root, "structMap")
    structMap.set("TYPE", "physical")
    structMapDiv = newChild(structMap, "div")

    createFileSec(path, sipFileGrp, structMapDiv)

    tree = etree.ElementTree(root)
    tree.write(XMLFile, pretty_print=True, xml_declaration=True)

    # Restore original path
    os.chdir(opath)
