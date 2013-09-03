#!/usr/bin/python2 -OO

import argparse
import datetime
from lxml import etree
from lxml.builder import ElementMaker
import os.path
import sys
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import fileOperations
from externals import checksummingTools


# TODO ask about what is duplicated for more files
# amdSec, techMD, file, fptr
def main(aip_uuid, aip_name, compression, sip_dir, aip_filename):

    # Prep work
    mets_schema_location = 'http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd'
    premis_schema_location = 'info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd'
    # Datetime format string from http://docs.python.org/2/library/datetime.html
    # %Y = 4 digit year, %m = 2 digit month, %d = 2 digit day
    # %H = 24-hour hour, %M = 2-digit minute, %S = 2 digit second
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    aip_identifier = aip_name+'-'+aip_uuid
    aip_path = os.path.join(sip_dir, aip_filename)
    # Get archive tool and version
    program, _ = compression.split('-')
    if program == '7z':
        archive_tool = '7-Zip'
        archive_tool_version = '9.20'  # TODO get this dynamically
    elif program == 'pbzip2':
        archive_tool = program
        archive_tool_version = '1.1.6'  # TODO get this dynamically
    # Format / file extension
    # TODO handle nested formats, eg. .tar.bz2
    format_name = '{} format'.format(compression)
    extension = os.path.splitext(aip_filename)[1]
    pronom_conversion = {
        '.7z': 'fmt/484',
        '.bz2': 'x-fmt/268',
        '.tar': 'x-fmt/265',
    }
    num_files = 1
    # Get size
    try:
        aip_size = os.path.getsize(aip_path)
    except os.error:
        print >> sys.stderr, "File {} does not exist or is inaccessible.  Aborting.".format(aip_path)
        return -1
    # Calculate checksum
    checksum_algorithm = 'sha256'
    checksum = checksummingTools.sha_for_file(aip_path)

    # Namespaces
    xsi = 'http://www.w3.org/2001/XMLSchema-instance'
    xlink = 'http://www.w3.org/1999/xlink'
    nsmap = {
        'xsi': xsi,
        'xlink': xlink,
    }
    # Set up structure
    E = ElementMaker(nsmap=nsmap)
    root = (
        E.mets(
            E.metsHdr(CREATEDATE=now),
            # amdSec goes here
            E.fileSec(
                E.fileGrp(),
            ),
            E.structMap(
                E.div(
                    TYPE="Archival Information Package",
                ),
                TYPE='physical'
            ),
        )
    )
    # Namespaced attributes have to be added separately - don't know how to do
    # inline with E
    root.attrib['{{{ns}}}schemaLocation'.format(ns=xsi)] = mets_schema_location

    add_amdsec_after = root.find('metsHdr')
    filegrp = root.iterdescendants(tag='fileGrp').next()
    div = root.iterdescendants(tag='div').next()
    # For each file, add amdSec, file, fptr
    for admin_id in range(1, num_files+1):

        # amdSec
        amdsec_id = 'amdSec_{}'.format(admin_id)
        amdsec = etree.Element('amdSec', ID=amdsec_id)
        amdsec = (
            E.amdSec(
                E.techMD(
                    E.mdWrap(
                        E.xmlData(
                        ),
                        MDTYPE='PREMIS:OBJECT',  # mdWrap
                    ),
                    ID='techMD_1',  # techMD
                ),
                ID='amdSec_{}'.format(admin_id),  # amdSec
            )
        )
        obj = (
            E.object(
                E.objectIdentifier(
                    E.objectIdentifierType('UUID'),
                    E.objectIdentifierValue(aip_uuid),
                ),
                E.objectCharacteristics(
                    E.compositionLevel('0'),
                    E.fixity(
                        E.messageDigestAlgorithm(checksum_algorithm),
                        E.messageDigest(checksum),
                    ),
                    E.size(str(aip_size)),
                    E.format(
                        E.formatDesignation(
                            E.formatName(format_name),
                            E.formatVersion(),
                        ),
                        E.formatRegistry(
                            E.formatRegistryName('PRONOM'),
                            E.formatRegistryKey(
                                pronom_conversion[extension])
                        ),
                    ),
                    E.creatingApplication(
                        E.creatingApplicationName(archive_tool),
                        E.creatingApplicationVersion(archive_tool_version),
                        E.dateCreatedByApplication(now),
                    ),
                ),
                version='2.2',
            )
        )
        obj.attrib['{{{ns}}}type'.format(ns=xsi)] = 'file'
        obj.attrib['{{{ns}}}schemaLocation'.format(ns=xsi)] = premis_schema_location
        # add obj as child of xmldata
        amdsec.iterdescendants(tag='xmlData').next().append(obj)
        # add amdSec after previous amdSec (or metsHdr if first one)
        add_amdsec_after.addnext(amdsec)

        add_amdsec_after = amdsec

        # fileGrp
        file_ = (
            E.file(
                E.FLocat(
                    LOCTYPE="OTHER",
                    OTHERLOCTYPE="SYSTEM",
                ),
                ID=aip_identifier,  # file
                ADMID=amdsec_id,
            )
        )
        filegrp.append(file_)
        flocat = file_.find('FLocat')
        flocat.attrib['{{{ns}}}href'.format(ns=xlink)] = aip_path

        # structMap
        fptr = etree.Element('fptr', FILEID=aip_identifier)
        div.append(fptr)

    # Write out pointer.xml
    xml_filename = 'pointer.xml'
    filename = os.path.join(os.path.dirname(aip_path), xml_filename)
    with open(filename, 'w') as f:
        f.write(etree.tostring(root, pretty_print=True))
    fileOperations.addFileToSIP(
        filePathRelativeToSIP='%SIPDirectory%'+xml_filename,
        fileUUID=str(uuid.uuid4()),
        sipUUID=aip_uuid,
        taskUUID=str(uuid.uuid4()),  # Unsure what should go here
        date=now,
        sourceType="aip creation",
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create AIP pointer file.')
    parser.add_argument('aip_uuid', type=str, help='%SIPUUID%')
    parser.add_argument('aip_name', type=str, help='%SIPName%')
    parser.add_argument('compression', type=str, help='%AIPCompressionAlgorithm%')
    parser.add_argument('sip_dir', type=str, help='%SIPDirectory%')
    parser.add_argument('aip_filename', type=str, help='%AIPFilename%')
    args = parser.parse_args()
    rc = main(args.aip_uuid, args.aip_name, args.compression, args.sip_dir, args.aip_filename)
    sys.exit(rc)
