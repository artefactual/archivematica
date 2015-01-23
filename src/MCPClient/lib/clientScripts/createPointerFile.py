#!/usr/bin/python2 -OO

import argparse
import datetime
from lxml import etree
from lxml.builder import ElementMaker
import os.path
import sys
import uuid

import archivematicaXMLNamesSpace as namespaces
import archivematicaCreateMETS2

# dashboard
from main.models import DublinCore

# archivematicaCommon
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
    program, algorithm = compression.split('-')

    # Pointer files are not written for uncompressed AIPs;
    # the purpose of the pointer file is primarily to provide information
    # on how to read a compressed AIP file, so there isn't anything for
    # it to do when pointing at an uncompressed AIP.
    if program == 'None':
        return 0

    if program == '7z':
        archive_tool = '7-Zip'
        archive_tool_version = '9.20'  # TODO get this dynamically
    elif program == 'pbzip2':
        archive_tool = program
        archive_tool_version = '1.1.6'  # TODO get this dynamically
    # Format / file extension
    _, extension = os.path.splitext(aip_filename)
    # PRONOM ID and PRONOM name for each file extension
    pronom_conversion = {
        '.7z': {'puid': 'fmt/484', 'name': '7Zip format'},
        '.bz2': {'puid': 'x-fmt/268', 'name': 'BZIP2 Compressed Archive'},
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
    # Get package type (AIP, AIC)
    sip_metadata_uuid = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'

    try:
        dc = DublinCore.objects.get(metadataappliestotype_id=sip_metadata_uuid,
                                    metadataappliestoidentifier=aip_uuid)
    except DublinCore.DoesNotExist:
        package_type = "Archival Information Package"
    else:
        package_type = dc.type

    # Namespaces
    nsmap = {
        # Default, unprefixed namespace
        None: namespaces.metsNS,
        'xsi': namespaces.xsiNS,
        'xlink': namespaces.xlinkNS,
    }
    # Set up structure
    E = ElementMaker(namespace=namespaces.metsNS, nsmap=nsmap)
    E_P = ElementMaker(namespace=namespaces.premisNS, nsmap={None: namespaces.premisNS})

    root = (
        E.mets(
            E.metsHdr(CREATEDATE=now),
            # amdSec goes here
            E.fileSec(
                E.fileGrp(USE='Archival Information Package'),
            ),
            E.structMap(
                TYPE='physical'
            ),
        )
    )
    # Namespaced attributes have to be added separately - don't know how to do
    # inline with E
    root.attrib[namespaces.xsiBNS+'schemaLocation'] = mets_schema_location

    add_amdsec_after = root.find('mets:metsHdr', namespaces=namespaces.NSMAP)
    filegrp = root.find('.//mets:fileGrp', namespaces=namespaces.NSMAP)
    structmap = root.find('.//mets:structMap', namespaces=namespaces.NSMAP)
    # For each file, add amdSec, file, fptr
    for admin_id in range(1, num_files+1):

        # amdSec
        amdsec_id = 'amdSec_{}'.format(admin_id)
        amdsec = E.amdSec(
            E.techMD(
                E.mdWrap(
                    E.xmlData(
                    ),
                    MDTYPE='PREMIS:OBJECT',  # mdWrap
                ),
                ID='techMD_1',  # techMD
            ),
            ID=amdsec_id,  # amdSec
        )
        # Add PREMIS:OBJECT
        obj = E_P.object(
            E_P.objectIdentifier(
                E_P.objectIdentifierType('UUID'),
                E_P.objectIdentifierValue(aip_uuid),
            ),
            E_P.objectCharacteristics(
                E_P.compositionLevel('1'),
                E_P.fixity(
                    E_P.messageDigestAlgorithm(checksum_algorithm),
                    E_P.messageDigest(checksum),
                ),
                E_P.size(str(aip_size)),
                E_P.format(
                    E_P.formatDesignation(
                        E_P.formatName(
                            pronom_conversion[extension]['name']),
                        E_P.formatVersion(),
                    ),
                    E_P.formatRegistry(
                        E_P.formatRegistryName('PRONOM'),
                        E_P.formatRegistryKey(
                            pronom_conversion[extension]['puid'])
                    ),
                ),
                E_P.creatingApplication(
                    E_P.creatingApplicationName(archive_tool),
                    E_P.creatingApplicationVersion(archive_tool_version),
                    E_P.dateCreatedByApplication(now),
                ),
            ),
            version='2.2',
        )
        obj.attrib[namespaces.xsiBNS+'type'] = 'file'
        obj.attrib[namespaces.xsiBNS+'schemaLocation'] = premis_schema_location

        # Add as child of xmldata
        amdsec.find('.//mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]/mets:xmlData', namespaces=namespaces.NSMAP).append(obj)

        # Add PREMIS:EVENT for compression, use archivematicaCreateMETS2 code
        elements = archivematicaCreateMETS2.createDigiprovMD(aip_uuid)
        for element in elements:
            amdsec.append(element)
        # Add PREMIS:AGENT for Archivematica
        elements = archivematicaCreateMETS2.createDigiprovMDAgents()
        for element in elements:
            amdsec.append(element)

        # add amdSec after previous amdSec (or metsHdr if first one)
        add_amdsec_after.addnext(amdsec)
        add_amdsec_after = amdsec

        # fileGrp
        file_ = E.file(
            E.FLocat(
                LOCTYPE="OTHER",
                OTHERLOCTYPE="SYSTEM",
            ),
            ID=aip_identifier
        )
        filegrp.append(file_)
        flocat = file_.find('mets:FLocat', namespaces=namespaces.NSMAP)
        flocat.attrib['{{{ns}}}href'.format(ns=namespaces.xlinkNS)] = aip_path

        # compression - 7z or tar.bz2
        if extension == '.7z':
            etree.SubElement(file_, "transformFile",
                TRANSFORMORDER='1',
                TRANSFORMTYPE='decompression',
                TRANSFORMALGORITHM=algorithm)
        elif extension == '.bz2':
            etree.SubElement(file_, "transformFile",
                TRANSFORMORDER='1',
                TRANSFORMTYPE='decompression',
                TRANSFORMALGORITHM='bzip2')
            etree.SubElement(file_, "transformFile",
                TRANSFORMORDER='2',
                TRANSFORMTYPE='decompression',
                TRANSFORMALGORITHM='tar')

        # structMap
        div = etree.SubElement(structmap, namespaces.metsBNS+'div', ADMID=amdsec_id, TYPE=package_type)
        etree.SubElement(div, namespaces.metsBNS+'fptr', FILEID=aip_identifier)

    print etree.tostring(root, pretty_print=True)

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
    return 0

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
