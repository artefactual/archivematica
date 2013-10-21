#! /usr/bin/python2 -OO

import argparse
import datetime
from lxml import etree
from lxml.builder import ElementMaker
import os
import re
import sys
import uuid

PATH = "/usr/lib/archivematica/archivematicaCommon"
if PATH not in sys.path:
    sys.path.append(PATH)
import databaseInterface
import fileOperations
import storageService as storage_service


def get_aip_info(aic_dir):
    """ Get AIP UUID, name and labels from objects directory and METS file. """
    aips = []
    aic_dir = os.path.join(aic_dir, 'objects')
    # Parse out AIP names and UUIDs
    # The only contents of the folder should be a bunch of files whose filenames
    # are AIP UUIDs, and the contents are the AIP name.
    uuid_regex = r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
    files = [d for d in os.listdir(aic_dir)
        if os.path.isfile(os.path.join(aic_dir, d))
        and re.match(uuid_regex, d)]
    for filename in files:
        file_path = os.path.join(aic_dir, filename)
        with open(file_path, 'r') as f:
            aip_name = f.readline()
        os.remove(file_path)
        aips.append({'name': aip_name, 'uuid': filename})

    # Fetch the METS file and parse out the Dublic Core metadata with the label
    nsmap = {
        'm': 'http://www.loc.gov/METS/',  # METS
        'dc': 'http://purl.org/dc/terms/',  # Dublin Core
    }
    for aip in aips:
        mets_in_aip = "{aip_name}-{aip_uuid}/data/METS.{aip_uuid}.xml".format(
            aip_name=aip['name'], aip_uuid=aip['uuid'])
        mets_path = os.path.join(aic_dir, "METS.{}.xml".format(aip['uuid']))
        storage_service.extract_file(aip['uuid'], mets_in_aip, mets_path)

        root = etree.parse(mets_path)
        aip['label'] = root.find('m:dmdSec/m:mdWrap/m:xmlData/dc:dublincore/dc:title',
            namespaces=nsmap).text

        os.remove(mets_path)

    print 'AIP info:', aips
    return aips

def get_aic_info(aic_uuid):
    """ Get AIC title and identifier. """
    title = identifier = ''
    sql = """SELECT title, identifier
             FROM Dublincore
             JOIN MetadataAppliesToTypes ON metadataAppliesToType = MetadataAppliesToTypes.pk
             WHERE MetadataAppliesToTypes.description = "SIP"
             AND metadataAppliesToidentifier='{uuid}';""".format(uuid=aic_uuid)
    rows = databaseInterface.queryAllSQL(sql)
    if rows:
        ((title, identifier),) = rows
    aic = {
        'uuid': aic_uuid,
        'title': title,
        'identifier': "AIC# {}".format(identifier) if identifier else '',
    }
    print 'AIC info:', aic
    return aic

def create_mets_file(aic, aips):
    """ Create AIC METS file with AIP information. """

    # Prepare constants
    nsmap = {
        None: 'http://www.loc.gov/METS/',  # METS
        'xlink': 'http://www.w3.org/1999/xlink',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    }
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Set up structure
    E = ElementMaker(namespace=None, nsmap=nsmap)
    mets = (
        E.mets(
            E.metsHdr(CREATEDATE=now),
            E.dmdSec(
                E.mdWrap(
                    E.xmlData(),
                    MDTYPE = "DC",  # mdWrap
                ),
                ID = 'dmdSec_1',  # dmdSec
            ),
            E.fileSec(
                E.fileGrp(),
            ),
            E.structMap(
                E.div(
                    TYPE = "Archival Information Collection",
                    DMDID = "dmdSec_1",
                ),
                TYPE = 'logical',  # structMap
            ),
        )
    )
    mets.attrib['{{{ns}}}schemaLocation'.format(ns=nsmap['xsi'])] = "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd"

    # Add Dublin Core info
    nsmap_dc = {None: 'http://purl.org/dc/terms/'}
    xml_data = mets.find('dmdSec/mdWrap/xmlData')
    # dublincore = etree.SubElement(xml_data, 'dublincore', nsmap=nsmap_dc)
    E_dc = ElementMaker(nsmap=nsmap_dc)
    dublincore = (
        E_dc.dublincore(
            E_dc.title(aic['title']),
            E_dc.type("Archival Information Collection"),
            E_dc.identifier(aic['identifier']),
        )
    )
    dublincore.attrib['{{{ns}}}schemaLocation'.format(ns=nsmap['xsi'])] = "http://purl.org/dc/terms/ http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd"
    xml_data.append(dublincore)

    # Add elements for each AIP
    file_grp = mets.find('fileSec/fileGrp')
    struct_div = mets.find('structMap/div')
    for aip in aips:
        file_id = '{name}-{uuid}'.format(name=aip['name'], uuid=aip['uuid'])
        etree.SubElement(file_grp, 'file', ID=file_id)

        div = etree.SubElement(struct_div, 'div', LABEL=aip['label'])
        etree.SubElement(div, 'fptr', FILEID=file_id)

    print etree.tostring(mets, pretty_print=True)

    # Write out the file
    basename = os.path.join('metadata', "METS-{}.xml".format(aic['uuid']))
    filename = os.path.join(aic['dir'], basename)
    with open(filename, 'w') as f:
        f.write(etree.tostring(mets, pretty_print=True))
    fileOperations.addFileToSIP(
        filePathRelativeToSIP='%SIPDirectory%'+basename,
        fileUUID=str(uuid.uuid4()),
        sipUUID=aic['uuid'],
        taskUUID=str(uuid.uuid4()),  # Unsure what should go here
        date=now,
        sourceType="aip creation",
    )


def create_aic_mets(aic_uuid, aic_dir):
    aips = get_aip_info(aic_dir)
    aic = get_aic_info(aic_uuid)
    aic['dir'] = aic_dir
    create_mets_file(aic, aips)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('aic_uuid', action='store', type=str, help="%SIPUUID%")
    parser.add_argument('aic_dir', action='store', type=str, help="%SIPDirectory%")
    args = parser.parse_args()
    create_aic_mets(args.aic_uuid, args.aic_dir)
