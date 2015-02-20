#!/usr/bin/python -OO

from __future__ import print_function
import os
import sys

from archivematicaCreateMETS import createFileSec, each_child
from archivematicaCreateMETS2 import createDigiprovMD
import archivematicaXMLNamesSpace as ns

from lxml import etree


def create_amdSecs(path, file_group_identifier, base_path, base_path_name, sip_uuid):
    amdSecs = []

    for child in each_child(path, file_group_identifier, base_path, base_path_name, sip_uuid):
        if isinstance(child, basestring):  # directory
            amdSecs.extend(create_amdSecs(child, file_group_identifier, base_path, base_path_name, sip_uuid))
        else:  # file
            admid = "digiprov-" + child.uuid
            amdSec = etree.Element(ns.metsBNS + 'amdSec',
                                   ID=admid)
            amdSec.extend(createDigiprovMD(child.uuid))
            amdSecs.append(amdSec)

    return amdSecs

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-s", "--basePath", action="store", dest="basePath", default="")
    parser.add_argument("-b", "--basePathString", action="store", dest="basePathString", default="SIPDirectory")  # transferDirectory
    parser.add_argument("-f", "--fileGroupIdentifier", action="store", dest="fileGroupIdentifier", default="sipUUID")  # transferUUID
    parser.add_argument("-S", "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_argument("-x", "--xmlFile", action="store", dest="xmlFile", default="")
    opts = parser.parse_args()

    if not os.path.exists(opts.xmlFile):
        print("Unable to find specified METS file:", opts.xmlFile, file=sys.stderr)
        sys.exit(1)

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        doc = etree.parse(opts.xmlFile, parser)
    except (etree.ParseError, etree.XMLSyntaxError):
        print("Unable to parse XML file at path:", opts.xmlFile, file=sys.stderr)
        sys.exit(1)

    fileGrp = doc.find(".//mets:fileSec/mets:fileGrp", namespaces=ns.NSMAP)

    root = doc.getroot()
    structMap = etree.SubElement(root, ns.metsBNS + "structMap",
                                 TYPE="physical",
                                 LABEL="processed")
    structMapDiv = etree.SubElement(structMap, ns.metsBNS + "div")

    basePathString = "%%%s%%" % (opts.basePathString)
    createFileSec(opts.basePath, opts.fileGroupIdentifier, opts.basePath, basePathString, fileGrp, structMapDiv, opts.sipUUID)

    # insert <amdSec>s after the <metsHdr>, which must be the first element
    # within the <mets> element if present.
    for el in create_amdSecs(opts.basePath, opts.fileGroupIdentifier, opts.basePath, basePathString, opts.sipUUID):
        root.insert(1, el)

    with open(opts.xmlFile, "w") as f:
        f.write(etree.tostring(doc,
                               pretty_print=True,
                               xml_declaration=True))
