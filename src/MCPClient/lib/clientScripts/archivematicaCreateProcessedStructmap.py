#!/usr/bin/python -OO

from __future__ import print_function
import os
import sys

from archivematicaCreateMETS import createFileSec
import archivematicaXMLNamesSpace as ns

from lxml import etree

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-s", "--basePath", action="store", dest="basePath", default="")
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

    structMap = etree.SubElement(doc.getroot(), ns.metsBNS + "structMap",
                                 TYPE="physical",
                                 LABEL="processed")
    structMapDiv = etree.SubElement(structMap, ns.metsBNS + "div")

    createFileSec(opts.basePath, fileGrp, structMapDiv)

    with open(opts.xmlFile, "w") as f:
        f.write(etree.tostring(doc,
                               pretty_print=True,
                               xml_declaration=True))
