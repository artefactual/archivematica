#!/usr/bin/env python2

from __future__ import print_function
import argparse
import collections
import csv
from lxml import etree
import os
import re
import sys

import archivematicaXMLNamesSpace as ns

# archivematicaCommon
import archivematicaFunctions
from custom_handlers import get_script_logger

def parseDmdSec(dmdSec, label='[Placeholder title]'):
    """
    Parses a dmdSec into a dict with child tag names and their values

    :param dmdSec: dmdSec elements
    :param label: Default title if not provided. Required by CONTENTdm
    :returns: Dict of {<child element tag>: [<value>, ...]
    """
    # If the dmdSec object is empty (i.e, no DC metadata has been assigned
    # in the dashboard, and there was no metadata.csv or other metadata file
    # in the transfer), return a placeholder title.
    if dmdSec is None:
        return collections.OrderedDict([('title', [label])])
    elementsDict = archivematicaFunctions.OrderedListsDict()

    # If we are dealing with a DOM object representing the Dublin Core metadata,
    # check to see if there is a title (required by CONTENTdm). If not, assign a
    # placeholder title.
    mdType = dmdSec.xpath('mets:mdWrap/@MDTYPE', namespaces=ns.NSMAP)
    if mdType == 'DC':
        dcTitlesDom = dmdSec.findall('.//dcterms:title', namespaces=ns.NSMAP)
        if not dcTitlesDom:
            elementsDict['title'] = label

    # Iterate over all descendants and put in the return dict
    # Key is the element's tag name, value is a list of the element's text
    xmldata = dmdSec.find('.//mets:xmlData', namespaces=ns.NSMAP)
    for element in xmldata.iterdescendants():
        tagname = element.tag
        # Strip namespace prefix
        # TODO can tag names be unicode?
        tagname = re.sub(r'{\S+}', '', tagname)  # \S = non whitespace
        if tagname in ('dublincore', ):
            continue
        elementsDict[tagname] = element.text or ''  # OrderedListsDict appends to lists as needed

    return collections.OrderedDict(elementsDict)


def getItemCountType(structMap):
    """
    Get whether this is a simple or compound DIP.

    Compound DIPs have metadata attached to directories, simple DIPs have
    metadata attached to files.

    :param structMap: structMap element from the METS file
    :return: String 'simple', 'compound-dirs' or 'compound-files'
    """
    divs_with_dmdsecs = structMap.findall('.//mets:div[@DMDID]', namespaces=ns.NSMAP)
    # If any are TYPE Directory, then it is compound
    if any([e.get('TYPE') == 'Directory' for e in divs_with_dmdsecs]):
        # If all are TYPE Directory then it is bulk
        if all([e.get('TYPE') == 'Directory' for e in divs_with_dmdsecs]):
            return 'compound-dirs'
        else:
            return 'compound-files'
    else:
        return 'simple'


def splitDmdSecs(dmdSecs):
    """
    Given a group of two dmdSecs, split them out.

    The 'dc' key will be a dmdSec with a MDTYPE='DC' and the 'nonDc' key will be
    a dmdSec with a MDTYPE='OTHER'. Both default to None.

    :param dmdSecs: 1- or 2-tuple of dmdSecs
    :return: Dict with {'dc': <dmdSec or None>, 'nonDc': <dmdSec or None>}
    """
    lenDmdSecs = len(dmdSecs)
    dmdSecPair = {'dc': None, 'nonDc': None}
    if lenDmdSecs > 2:
        print('Error splitting dmdSecs, more than 2 provided', file=sys.stderr)
        return dmdSecPair
    for dmdSec in dmdSecs:
        mdWrap = dmdSec.find('mets:mdWrap', namespaces=ns.NSMAP)
        if mdWrap.get('MDTYPE') == 'OTHER':
            dmdSecPair['nonDc'] = parseDmdSec(dmdSec)
        if mdWrap.get('MDTYPE') == 'DC':
            dmdSecPair['dc'] = parseDmdSec(dmdSec)
    if lenDmdSecs == 0:
        # If dmdSecs is empty, let parseDcXML() assign a placeholder title in dcMetadata.
        dmdSecPair['dc'] = parseDmdSec(None)

    return dmdSecPair


def addAipUuidToDcMetadata(dipUuid, dcMetadata):
    """
    Add the AIP UUID to the DC metadata.

    :param dipUuid: UUID of the AIP to add as the identifier.
    :param dcMetadata: Metadata dict to add identifier to, or None.
    """
    if not dcMetadata:
        return None
    if 'identifier' not in dcMetadata:
        dcMetadata['identifier'] = [dipUuid]
    else:
        dcMetadata['identifier'].append(dipUuid)
    return dcMetadata


def generate_project_client_package(output_dir, package_type, structmap, dmdsecs, dipuuid):
    """
    Generates a simple.txt or compound.txt from the METS of a DIP

    :param output_dir: Path to directory for simple/compound.txt
    :param structmap: structMap element from the METS (Preparse somehow?)
    :param dmdsecs: Dict of {<DMDID>: OrderedDict{column name: value} or <dmdSec element>? }
    :param dipuuid: UUID of the DIP
    """
    print('DIP UUID:', dipuuid)

    if 'compound' in package_type:
        csv_path = os.path.join(output_dir, 'compound.txt')
    else:
        csv_path = os.path.join(output_dir, 'simple.txt')

    print('Package type:', package_type)
    print('Path to the output tabfile', csv_path)

    divs_with_dmdsecs = structmap.findall('.//mets:div[@DMDID]', namespaces=ns.NSMAP)
    with open(csv_path, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter='\t')

        # Iterate through every div and create a row for each
        csv_header_ref = None
        for div in divs_with_dmdsecs:
            # Find associated dmdSecs
            dmdids = div.get('DMDID').split()
            # Take nonDC dmdSec, fallback to DC dmdSec
            dmdsecpair = splitDmdSecs([dmdsecs[dmdid] for dmdid in dmdids])
            dmdsecpair['dc'] = addAipUuidToDcMetadata(dipuuid, dmdsecpair['dc'])
            metadata = dmdsecpair['nonDc'] or dmdsecpair['dc']
            # Create csv_header and csv_values from the dmdSec metadata
            csv_header = []
            csv_values = []
            for header, value in metadata.iteritems():
                csv_header.append(header)
                value = '; '.join(value).replace('\r', '').replace('\n', '')
                csv_values.append(archivematicaFunctions.unicodeToStr(value))

            # Add AIP UUID
            csv_header.append('AIP UUID')
            csv_values.append(dipuuid)

            # Add file UUID
            csv_header.append('file UUID')
            if 'dirs' in package_type:
                # Directories have no file UUID
                csv_values.append('')
            else:
                file_uuid = ''
                fptr = div.find('mets:fptr', namespaces=ns.NSMAP)
                # Only files have fptrs as direct children
                if fptr is not None:
                    # File UUID is last 36 characters of FILEID
                    file_uuid = fptr.get('FILEID')[-36:]
                csv_values.append(file_uuid)

            # Add file or directory name
            name = div.attrib['LABEL']  # Fallback if LABEL doesn't exist?
            if 'dirs' in package_type:
                csv_header.insert(0, 'Directory name')
                csv_values.insert(0, name)
            else:
                csv_header.append('Filename')
                csv_values.append(name)

            # Compare csv_header, if diff ERROR (first time set, write to file)
            if csv_header_ref and csv_header_ref != csv_header:
                print('ERROR headers differ,', csv_path, 'almost certainly invalid', file=sys.stderr)
                print('Reference header:', csv_header_ref, file=sys.stderr)
                print('Differing header:', csv_header, file=sys.stderr)
                return 1
            # If first time through, write out header
            if not csv_header_ref:
                csv_header_ref = csv_header
                writer.writerow(csv_header_ref)
                print('Tabfile header:', csv_header)
            # Write csv_row
            writer.writerow(csv_values)
            print('Values:', csv_values)
    return 0

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.restrutureDIPForContentDMUpload")

    parser = argparse.ArgumentParser(description='restructure')
    parser.add_argument('--uuid', action="store", dest='uuid', metavar='UUID', help='%SIPUUID%')
    parser.add_argument('--dipDir', action="store", dest='dipDir', metavar='dipDir', help='%SIPDirectory%')

    args = parser.parse_args()
    # FIXME move more of this to a main function - only parse the args in the if __name__==__main__

    # Perform some preliminary validation on the argument values.
    if not os.path.isdir(args.dipDir):
        print("Can't find", args.dipDir, ', exiting.')
        sys.exit(1)

    # Read and parse the METS file.
    metsFile = os.path.join(args.dipDir, 'METS.' + args.uuid + '.xml')
    root = etree.parse(metsFile)

    # If there is a user-submitted structMap (i.e., len(structMapts) is 2, use that one.
    # QUESTION why not use physical structMap always?
    structMaps = root.findall('mets:structMap', namespaces=ns.NSMAP)
    archivematica_structmap = structMaps[0]
    if len(structMaps) == 2:
        itemCountType = getItemCountType(structMaps[1])
    else:
        itemCountType = getItemCountType(archivematica_structmap)

    # Get the dmdSec nodes from the METS file.
    dmdsecs = {e.get('ID'): e for e in root.findall('mets:dmdSec', namespaces=ns.NSMAP)}

    sys.exit(generate_project_client_package(os.path.join(args.dipDir, 'objects'), itemCountType, archivematica_structmap, dmdsecs, args.uuid))
