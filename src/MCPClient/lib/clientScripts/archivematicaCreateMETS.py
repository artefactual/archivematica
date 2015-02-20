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
from xml.sax.saxutils import quoteattr

import archivematicaXMLNamesSpace as ns

# dashboard
from main.models import File

# archivematicaCommon
from archivematicaFunctions import escape
from databaseFunctions import getAccessionNumberFromTransfer, getUTCDate
from elasticSearchFunctions import getDashboardUUID


def createMetsHdr(sip_uuid):
    header = etree.Element(ns.metsBNS + "metsHdr",
                           CREATEDATE=getUTCDate().split(".")[0])
    agent = etree.SubElement(header, ns.metsBNS + "agent",
                             ROLE="CREATOR",
                             TYPE="OTHER",
                             OTHERTYPE="SOFTWARE")
    name = etree.SubElement(agent, ns.metsBNS + "name")
    name.text = getDashboardUUID()
    note = etree.SubElement(agent, ns.metsBNS + "note")
    note.text = "Archivematica dashboard UUID"

    accession_number = getAccessionNumberFromTransfer(sip_uuid)
    if accession_number:
        alt_id = etree.SubElement(header, ns.metsBNS + "altRecordID",
                                  TYPE="Accession number")
        alt_id.text = accession_number

    return header


def newChild(parent, tag, text=None, tailText=None):
    child = etree.Element(tag)
    parent.append(child)
    child.text = text
    return child


def each_child(path, file_group_identifier, base_path, base_path_name, sip_uuid):
    """
    Iterates over entries in a filesystem, beginning at `path`.

    At each entry in the filesystem, yields either a File model instance
    (for files) or a string (for directories).

    When iterating, makes two passes: first iterating over files, then
    directories. Does not iterate over directories; consumers should
    call this function again on directory strings to recurse.

    :param string path: path to a directory on disk to recurse into.
    :raises ValueError: if the specified path does not exist, or is not a directory.
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise ValueError("Specified path {} does not exist!".format(path))
    elif os.path.isfile(path):
        raise ValueError("Specified path {} is a file, not a directory!".format(path))

    for doDirectories in [False, True]:
        directoryContents = sorted(os.listdir(path))
        for item in directoryContents:
            itempath = os.path.join(path, item)
            if os.path.isdir(itempath):
                if not doDirectories:
                    continue

                yield itempath
            elif os.path.isfile(itempath):
                if doDirectories:
                    continue

                pathSTR = itempath.replace(base_path, base_path_name, 1)
                kwargs = {
                    'removedtime__isnull': True,
                    file_group_identifier: sip_uuid,
                    'currentlocation': pathSTR
                }
                try:
                    yield File.objects.get(**kwargs)
                except File.DoesNotExist:
                    print >> sys.stderr, "No uuid for file: \"", pathSTR, "\""


#Do /SIP-UUID/
#Force only /SIP-UUID/objects
doneFirstRun = False
def createFileSec(path, file_group_identifier, base_path, base_path_name, parentBranch, structMapParent, sip_uuid):
    print >>sys.stderr, "createFileSec: ", path, parentBranch, structMapParent
    doneFirstRun = True
    pathSTR = path.__str__()
    pathSTR = path.__str__()
    if pathSTR == base_path + "objects/": #IF it's it's the SIP folder, it's OBJECTS
        pathSTR = "objects"
    #pathSTR = string.replace(path.__str__(), "/tmp/" + sys.argv[2] + "/" + sys.argv[3], "objects", 1)
    #if pathSTR + "/" == basePath: #if it's the very first run through (recursive function)
    if path == base_path: #if it's the very first run through (recursive function)
        pathSTR = os.path.basename(os.path.dirname(base_path))
        #structMapParent.set("DMDID", "SIP-description")

        #currentBranch = newChild(parentBranch, "fileGrp")
        #currentBranch.set("USE", "directory")
        # structMap directory
        div = newChild(structMapParent, ns.metsBNS + "div")
        createFileSec(os.path.join(path, "objects/"), file_group_identifier, base_path, base_path_name, parentBranch, div, sip_uuid)
        doneFirstRun = False
    filename = os.path.basename(pathSTR)

    structMapParent.set("TYPE", "directory")
    structMapParent.set("LABEL", escape(filename))

    if doneFirstRun:
        for item in each_child(path, file_group_identifier, base_path, base_path_name, sip_uuid):
            if isinstance(item, File):
                pathSTR = item.currentlocation.replace('%transferDirectory%', "", 1)

                ID = "file-" + item.uuid.__str__()

                # structMap file
                fptr = newChild(structMapParent, ns.metsBNS + "fptr")
                FILEID = "file-" + item.uuid.__str__()
                fptr.set("FILEID", escape(FILEID))

                # If the file already exists in the fileSec, don't create
                # a second entry.
                fileI = parentBranch.find('./mets:file[@ID="{}"]'.format(ID), namespaces=ns.NSMAP)
                if fileI is None:
                    fileI = etree.SubElement(parentBranch, ns.metsBNS + "file")

                    filename = ''.join(quoteattr(pathSTR).split("\"")[1:-1])

                    fileI.set("ID", escape(ID))

                    Flocat = newChild(fileI, ns.metsBNS + "FLocat")
                    Flocat.set(ns.xlinkBNS + "href", escape(pathSTR))
                    Flocat.set("LOCTYPE", "OTHER")
                    Flocat.set("OTHERLOCTYPE", "SYSTEM")

                    # used when adding amdSecs at a later time
                    admid = "digiprov-" + item.uuid
                    fileI.set("ADMID", admid)

            else:
                div = newChild(structMapParent, ns.metsBNS + "div")
                createFileSec(os.path.join(path, item), file_group_identifier, base_path, base_path_name, parentBranch, div, sip_uuid)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-s", "--basePath", action="store", dest="basePath", default="")
    parser.add_option("-b", "--basePathString", action="store", dest="basePathString", default="SIPDirectory")  # transferDirectory
    parser.add_option("-f", "--fileGroupIdentifier", action="store", dest="fileGroupIdentifier", default="sipUUID")  # transferUUID
    parser.add_option("-S", "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-x", "--xmlFile", action="store", dest="xmlFile", default="")
    (opts, args) = parser.parse_args()
    print opts

    root = etree.Element(ns.metsBNS + "mets",
        nsmap={"xlink": ns.xlinkNS, "mets": ns.metsNS},
        attrib={
            ns.xsiBNS + "schemaLocation": "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd",
            "OBJID": opts.sipUUID
        }
    )

    root.append(createMetsHdr(opts.sipUUID))

    #cd /tmp/$UUID;
    opath = os.getcwd()
    os.chdir(opts.basePath)
    path = opts.basePath

    fileSec = etree.Element(ns.metsBNS + "fileSec")
    #fileSec.tail = "\n"
    root.append(fileSec)

    sipFileGrp = etree.SubElement(fileSec, ns.metsBNS + "fileGrp")
    sipFileGrp.set("USE", "original")

    structMap = newChild(root, ns.metsBNS + "structMap")
    structMap.set("TYPE", "physical")
    structMap.set("LABEL", "original")
    structMapDiv = newChild(structMap, ns.metsBNS + "div")

    basePathString = "%%%s%%" % (opts.basePathString)
    createFileSec(path, opts.fileGroupIdentifier, opts.basePath, basePathString, sipFileGrp, structMapDiv, opts.sipUUID)

    tree = etree.ElementTree(root)
    tree.write(opts.xmlFile, pretty_print=True, xml_declaration=True)

    # Restore original path
    os.chdir(opath)
