#!/usr/bin/python -OO

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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Mark Jordan <mark2jordan@gmail.com>

from __future__ import print_function
import argparse
import collections
import csv
import glob
import json
from lxml import etree
import os
import re
import shutil
import sys
import urllib

import archivematicaXMLNamesSpace as ns

# archivematicaCommon
import archivematicaFunctions
from archivematicaFunctions import normalizeNonDcElementName

# Create the output dir for the CONTENTdm DIP and return the resulting path.
# importMethod is either 'projectclient' or 'directupload'.
def prepareOutputDir(outputDipDir, importMethod, dipUuid):
    outputDipDir = os.path.join(outputDipDir, 'CONTENTdm', importMethod, dipUuid)
    # Check for and then delete a subdirectory named after the current package. We always want
    # a clean output directory for the import package.
    if os.path.exists(outputDipDir):
        shutil.rmtree(outputDipDir)
    os.makedirs(outputDipDir)
    return outputDipDir


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


# Takes in a DOM object containing the METS structMap, returns a dictionary with 
# fptrValue : [ order, dmdSec, label, filename ] members.
# Files in the DIP objects directory start with the UUID (i.e., first 36 characters 
# of the filename) # of the of the file named in the fptr FILEID in the structMap; 
# each file ends in the UUID. Also, we are only interested in divs that are direct
# children of a div with TYPE=Directory and LABEL=objects:
#  <div TYPE="Directory" LABEL="DigitizationOutput-50a3c71f-92d6-46d1-98ce-8227caa79f85-50a3c71f-92d6-46d1-98ce-8227caa79f85">
#     <div TYPE="Directory" LABEL="objects" DMDID="dmdSec_1">
#       <div LABEL="Page 1">
#         <fptr FILEID="P1050152.JPG-e2d0cd78-f1b9-446b-81ae-ea0e282332bb"/>
#       </div>
def parseStructMap(structMap, filesInObjectDirectory):
    structMapDict = {}
    # Get filenames of all the files in the objects directory (recursively);
    # filesInObjectDirectory contains paths, but we need to get the filename only
    # for the structMap checking. Add each filename to structMapDict.
    filesInObjectDir = []
    for file in filesInObjectDirectory:
        if file is not None:
            head, tail = os.path.split(file)
            filesInObjectDir.append(tail)
        
    # Get all the fptr elements.
    fptrOrder = 0
    for node in structMap.getElementsByTagNameNS('*', 'fptr'):
        for k, v in node.attributes.items():
            if k == 'FILEID':
                # DMDID is an attribute of the file's parent div.
                parentDivDmdId = node.parentNode.getAttribute('DMDID')
                filename = getFptrObjectFilename(v, filesInObjectDir)
                # We only want entries for files that are in the objects directory.
                if filename is not None:
                    parentDivLabel = node.parentNode.getAttribute('LABEL')
                    # If the parent div doesn't have a LABEL, use the filesname as the label.
                    if not len(parentDivLabel):
                        parentDivLabel = filename
                    fptrOrder = fptrOrder + 1
                    structMapDict[v] = {
                        # Python has no natsort, so we padd fptOrder with up to
                        # 4 zeros to make it more easily sortable.
                        'order' : str(fptrOrder).zfill(5),
                        'filename' : filename,
                        'label' : parentDivLabel,
                        'dmdSec' : parentDivDmdId
                    }

    return structMapDict


# Given a ftpr FILEID value (which looks like this: P1050154.JPG-09869659-fc89-46ce-ad1c-fe166becccca),
# return the name of the corresponding file from the DIP objects directory.
def getFptrObjectFilename(fileId, filesInObjectDir):
    # Assumes UUID is the last 36 characters of the fptr value.
    uuid = fileId[-36:]
    for filename in filesInObjectDir:
        if uuid in filename:
            return filename


# Generate a dictionary containing 1) 'dcMappings', a nested dictionary with DCTERMS
# elememts as keys, each of which has as its values the CONTENTdm nick and name for
# the corresponding field in the current collection and 2), 'nonDcMappings', a nested
# disctionary with field names (i.e., labels) as keys, each of which has as its values
# the CONTENTdm nick and name for the corresponding field in the collection, and 3), 
# 'order', a list of the collection's field nicks in the order they exist in the
# collection's configuration, which is needed to write out the metadata in the correct
# field order. The Archivematica metadata CRUD form only uses the legacy unqualified
# DC elements but we include the entire CONTENTdm DCTERMS mappings because the entire
# set of DCTERMS are supported in dublincore.xml files included in the transfer
# package's metadata directory and in bulk transfer metadata.csv files.
def getContentdmCollectionFieldInfo(contentdmServer, targetCollection):
    collectionFieldInfo = {}
    # First, define the CONTENTdm DC nicknames -> DCTERMs mapping. 
    contentdmDctermsMap = {
         'describ' : 'abstract',
         'rightsa' : 'accessRights',
         'accrua' : 'accrualMethod',
         'accrub' : 'accrualPeriodicity',
         'accruc' : 'accrualPolicy',
         'titlea' : 'alternative',
         'audien' : 'audience',
         'datec' : 'available',
         'identia' : 'bibliographicCitation',
         'relatim' : 'conformsTo',
         'contri' : 'contributor',
         'covera' : 'coverage',
         'datea' : 'created',
         'creato' : 'creator',
         'date' : 'date',
         'datef' : 'dateAccepted',
         'dateg' : 'dateCopyrighted',
         'dateh' : 'dateSubmitted',
         'descri' : 'description',
         'audienb' : 'educationLevel',
         'formata' : 'extent',
         'format' : 'format',
         'relatil' : 'hasFormat',
         'relatih' : 'hasPart',
         'relatib' : 'hasVersion',
         'identi' : 'identifier',
         'instru' : 'instructionalMethod',
         'relatik' : 'isFormatOf',
         'relatig' : 'isPartOf',
         'relatii' : 'isReferencedBy',
         'relatic' : 'isReplacedBy',
         'relatie' : 'isRequiredBy',
         'relatia' : 'isVersionOf',
         'dated' : 'issued',
         'langua' : 'language',
         'rightsb' : 'license',
         'audiena' : 'mediator',
         'formatb' : 'medium',
         'datee' : 'modified',
         'proven' : 'provenance',
         'publis' : 'publisher',
         'relatij' : 'references',
         'relati' : 'relation',
         'relatid' : 'replaces',
         'relatif' : 'requires',
         'rights' : 'rights',
         'rightsc' : 'rightsHolder',
         'source' : 'source',
         'coveraa' : 'spatial',
         'subjec' : 'subject',
         'descria' : 'tableOfContents',
         'coverab' : 'temporal',
         'title' : 'title',
         'type' : 'type',
         'dateb' : 'valid',
    }
    # Query CONTENTdm to get the target collection's field configurations.
    CollectionFieldConfigUrl = contentdmServer + '?q=dmGetCollectionFieldInfo' + targetCollection + '/json'
    try:
        f = urllib.urlopen(CollectionFieldConfigUrl)
        collectionFieldConfigString = f.read()
        collectionFieldConfig = json.loads(collectionFieldConfigString)
    except:
        print "Cannot retrieve CONTENTdm collection field configuration from " + CollectionFieldConfigUrl
        sys.exit(1)

    # We separate out the fields that are mapped to a DC field in the CONTENTdm
    # collection's configuration, so we can fall back on these fields if there
    # is no CONTENTdm collection specific metadata, e.g. when the transfer had no
    # metadata.csv file and DC metadata was added manually in the dashboard.
    # For the DC mappings, we want a dict containing items that looks like
    # { 'contributor': { 'name': u'Contributors', 'nick': u'contri'},
    # 'creator': { 'name': u'Creator', 'nick': u'creato'},
    # 'date': { 'name': u'Date', 'nick': u'dateso'}, [...] }. Is is possible
    # that more than one CONTENTdm field is mapped to the same DC element;
    # in this case, we take the last mapping and ignore the rest, since there is
    # no way to tell which should take precedence. The non-DC mappings have
    # the field name as their key, like "u'CONTENTdm number': { 'name': 
    # u'CONTENTdm number', 'nick': u'dmrecord'} (i.e., key and 'name' are the same).
    collectionFieldDcMappings = {}
    collectionFieldNonDcMappings = {}
    # We also want a simple list of all the fields in the current collection, in the order
    # they exist in the collection's CONTENTdm configuration.
    collectionFieldOrder = []
    # Define a set of CONTENTdm-generated fields that we don't want to show up in the mappings.
    systemFields = ['fullrs', 'dmoclcno', 'dmcreated', 'dmmodified', 'dmrecord', 'find']
    for fieldConfig in collectionFieldConfig:
        fieldName = fieldConfig['name']
        # For fields that have a DC mapping.
        if fieldConfig['dc'] != 'BLANK' and fieldConfig['dc'] != '':
            collectionFieldDcMappings[contentdmDctermsMap[fieldConfig['dc']]] = {'nick' : fieldConfig['nick'] , 'name' : fieldName}
        # For all fields. 'NonDc' is used here to mean 'general', not to signify
        # that the field doesn't have a DC mapping.
        collectionFieldNonDcMappings[fieldName] = {'nick' : fieldConfig['nick'] , 'name' : fieldName}
        if fieldConfig['nick'] not in systemFields:
            collectionFieldOrder.append(fieldConfig['nick'])
    collectionFieldInfo['dcMappings'] = collectionFieldDcMappings
    collectionFieldInfo['nonDcMappings'] = collectionFieldNonDcMappings
    collectionFieldInfo['order'] = collectionFieldOrder
    return collectionFieldInfo


def getObjectDirectoryFiles(objectDir):
    """
    Get a list of all the files (recursive) in the provided directory.

    "Even though there can be subdirectories in the objects directory,
    assumes each file should have a unique name." What does this mean?

    :param str objectDir: Full path to the objects directory
    :returns: List of full paths to files in objectDir
    """
    fileList = []
    for dirname, _, files in os.walk(objectDir):
        for f in files:
            fileList.append(os.path.join(dirname, f))
    return fileList

# Generate a .desc file used in CONTENTdm 'direct import' packages. Use dcMetadata only
# if nonDcMetadata is empty.
# .desc file looks like this:
# <?xml version="1.0" encoding="utf-8"?>
# <itemmetadata>
# <title>wall</title>
#  [... every collection field nick, empty and with values]
# <is></is>
# <transc></transc>
# <fullrs />
# <dmoclcno></dmoclcno>
# <dmcreated></dmcreated>
# <dmmodified></dmmodified>
# <dmrecord></dmrecord>
# <find></find>
# <dmimage></dmimage>
# <dmad1></dmad1>
# <dmad2></dmad2>
# <dmaccess></dmaccess>
# </xml>
def generateDescFile(dcMetadata, nonDcMetadata, dipUuid = None):
    collectionFieldInfo = getContentdmCollectionFieldInfo(args.contentdmServer, args.targetCollection)
    output = '<?xml version="1.0" encoding="utf-8"?>' + "\n"
    output += "<itemmetadata>\n"

    # Process the non-DC metadata, if there is any.
    if nonDcMetadata is not None:
        # Populate the AIP UUID field in the non-DC metadata with the last 36 characters of the SIP name.
        if dipUuid is not None:
            aipUuidValues = []
            aipUuidValues.append(dipUuid[-36:])
            nonDcMetadata['aip_uuid'] = aipUuidValues
        # Define a list of elements we don't want to add based on their presence in the collection's
        # field config, since we add them in the template at the end of this function.
        doNotAdd = ['transc', 'fullrs', 'dmoclcno', 'dmcreated', 'dmmodified', 'dmrecord',
            'find', 'dmimage', 'dmad1', 'dmad2', 'dmaccess']
        for element in collectionFieldInfo['nonDcMappings'].keys():
            # If a field is in the incoming item non-DC metadata, populate the corresponding
            # tag with its 'nick' value.
            # First, normalize CONTENTdm field names so they can match element names in the
            # metadata. We need to do this because the raw (i.e., human readable field names)
            # are used as field keys in collectionFieldInfo['nonDcMappings'].
            normalizedElement = normalizeNonDcElementName(element)
            if normalizedElement in nonDcMetadata.keys():
                values = ''
                output += '<' + collectionFieldInfo['nonDcMappings'][element]['nick'] + '>'
                # Repeated values in CONTENTdm metadata need to be separated with semicolons.
                if len(nonDcMetadata[normalizedElement]) == 1:
                    output += nonDcMetadata[normalizedElement][0]
                if len(nonDcMetadata[normalizedElement]) > 1:
                    output += '; '.join(nonDcMetadata[normalizedElement])
                output += '</' + collectionFieldInfo['nonDcMappings'][element]['nick'] + ">\n"
            # We need to include elements that are in the collection field config but
            # that do not have any values for the current item.
            else:
                if collectionFieldInfo['nonDcMappings'][element]['nick'] not in doNotAdd:
                    output += '<' + collectionFieldInfo['nonDcMappings'][element]['nick'] + '></' + collectionFieldInfo['nonDcMappings'][element]['nick'] + ">\n"

    # I.e., there is no non-DC metadata.
    else:
        # If there is no non-DC metadata, process the DC metadata. Loop through the collection's 
        # field configuration and generate XML elements for all its fields.
        # We treat 'identifier' separately because we populate it with the AIP UUID.
        if dipUuid is not None:
            if 'identifier' not in dcMetadata:
                dcMetadata['identifier'] = [dipUuid[-36:]]
            else:
                if len(dcMetadata['identifier']):
                    dcMetadata['identifier'].append(dipUuid[-36:])
                else:
                    dcMetadata['identifier'] = dipUuid[-36:]
        for dcElement in collectionFieldInfo['dcMappings'].keys():
            # If a field is in the incoming item dcMetadata, populate the corresponding tag
            # with its 'nick' value.
            if dcElement in dcMetadata.keys():
                output += '<' + collectionFieldInfo['dcMappings'][dcElement]['nick'] + '>'
                # Repeated values in CONTENTdm metadata need to be separated with semicolons.
                if len(dcMetadata[dcElement]) == 1:
                    output += dcMetadata[dcElement][0]
                if len(dcMetadata[dcElement]) > 1:
                    output += '; '.join(dcMetadata[dcElement])
                output += '</' + collectionFieldInfo['dcMappings'][dcElement]['nick'] + ">\n"
            # We need to include elements that are in the collection field config but
            # that do not have any values for the current item.
            else:
                output += '<' + collectionFieldInfo['dcMappings'][dcElement]['nick'] + '></' + collectionFieldInfo['dcMappings'][dcElement]['nick'] + ">\n"

    # These fields are boilerplate in new .desc files.          
    output += "<transc></transc>\n"
    output += "<fullrs />\n"
    output += "<dmoclcno></dmoclcno>\n"
    output += "<dmcreated></dmcreated>\n"
    output += "<dmmodified></dmmodified>\n"
    output += "<dmrecord></dmrecord>\n"
    output += "<find></find>\n"
    output += "<dmimage></dmimage>\n"
    output += "<dmad1></dmad1>\n"
    output += "<dmad2></dmad2>\n"
    output += "<dmaccess></dmaccess>\n"
    output += "</xml>\n"
    return output

# Performs an XSL transformation on the user-supplied structMap, outputting
# the contents of an index.cpd file for use in the Direct Upload DIP.
def transformUserSuppliedStructMap(structMap):
    print structMap
    mets_tree = etree.XML(structMap)
    xsl_tree = etree.XML('''\
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<!--
XSL stylesheet to convert a METS structMap into a CONTENTdm 'monograph' hierarchical
.cpd file. Assumes that child items use METS div LABEL attributes with value 'page'.
-->

<xsl:output method = "xml" encoding = "utf-8" indent = "yes" omit-xml-declaration="yes" />
<xsl:template match = "structMap">
    <cpd>
    <!-- Insert a newline after cpd. -->
    <xsl:text>
    </xsl:text>
    <type>Monograph</type>
    <xsl:apply-templates/>
    </cpd>
</xsl:template>

<!-- Assumes that child items use METS div LABEL attributes with value 'page'. -->
<xsl:template match = "div[@TYPE = 'page']">
  <page>
    <!-- Insert a newline after page. -->
    <xsl:text>
    </xsl:text>  
    <pagetitle><xsl:value-of select = "@LABEL"/></pagetitle>
    <xsl:apply-templates/>
  </page>
</xsl:template>

<xsl:template match = "div[@TYPE != 'page']">
  <node>
    <!-- Insert a newline after node. -->
    <xsl:text>
    </xsl:text>  
    <nodetitle><xsl:value-of select = "@LABEL"/></nodetitle>
    <xsl:apply-templates/>
  </node>
</xsl:template>

<xsl:template match = "fptr">
    <pagefile><xsl:value-of select="@FILEID" /></pagefile>
    <!-- Insert a newline between pagefile and pageptr. -->
    <xsl:text>
    </xsl:text>
    <pageptr>+</pageptr>
</xsl:template>

</xsl:stylesheet>''')
    transform = etree.XSLT(xsl_tree)
    result = transform(mets_tree)
    return result


# Generate an object file's entry in the .full file.
def generateFullFileEntry(title, filename, extension):
    fullFileContent = "<item>\n"
    fullFileContent += "  <title>" + title + "</title>\n"
    fullFileContent += "  <object>" + filename + extension + "</object>\n"
    fullFileContent += "  <desc>" + filename + ".desc</desc>\n"
    fullFileContent += "  <icon>" + filename + ".icon</icon>\n"
    fullFileContent += "  <update>0</update>\n  <info>nopdf</info>\n"
    fullFileContent += "</item>\n"
    return fullFileContent


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


def groupDmdSecs(dmdSecs, structMap):
    """
    Group dmdSecs by what structMap div they are associated with.

    Group the dmdSecs into item-specific pairs of DC and OTHER, or single-item
    groups of either if the other type is absent.

    :param dmdSecs: List of dmdSec elements
    :returns: List of 1- or 2-tuples of dmdSecs belonging to the same Item, or empty list
    """
    # IDEA Return dict of {'dc': <dmdSec or None>, 'nonDc': <dmdSec or None>} so that splitDmdSecs (below) is not needed
    grouped_dmdsecs = []
    dmdsecs_dict = {e.get('ID'): e for e in dmdSecs}

    # Get all divs with DMDID
    divs_with_dmdsecs = structMap.findall('.//mets:div[@DMDID]', namespaces=ns.NSMAP)
    # For each div, get dmdSecs associated, add to return
    for elem in divs_with_dmdsecs:
        dmdids = elem.get('DMDID').split()
        group = tuple(dmdsecs_dict[dmdid] for dmdid in dmdids)
        grouped_dmdsecs.append(group)

    return grouped_dmdsecs


def splitDmdSecs(dmdSecs):
    """
    Given a group of two dmdSecs, split them out so they can be passed to
    generateDescFile() with the expected values.

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


def getFileIdsForDmdSec(structMaps, dmdid):
    """
    Given a list of structMaps and a DMDID value, return a list of all the
    <fptr> values for the files named in the structMap corresponding to
    to the DMDID.

    :param structMaps: List of structMaps in this METS file
    :param dmdid: DMDID to find the associated file(s) for
    :return: List of FILEIDs associated with the dmdid
    """
    all_fileids = []
    # We use the Archivematica default structMap, which is always the first.
    structMap = structMaps[0]
    # Find the div with the associated DMDID
    divs = structMap.xpath('.//mets:div[contains(@DMDID, "' + dmdid + '")]', namespaces=ns.NSMAP)
    for d in divs:
        # Handle false positives from dmdSec_1 vs dmdSec_10
        if d.get('DMDID') != dmdid:
            divs.remove(d)
        # Get the FILEID from all fptrs that are chlidren
        fileids = d.xpath('.//mets:fptr/@FILEID', namespaces=ns.NSMAP)
        all_fileids.extend(fileids)

    return all_fileids


def getFilesInObjectDirectoryForThisDmdSecGroup(dmdSecGroup, structMaps):
    """
    Given a group of dmdSecs and the METS structMaps, return a list of files
    that are described by the dmdSecs.

    :param dmdSecGroup: 1- or 2-tuple of dmdSec objects corresponding to the same file or folder
    :param structMaps: List of all structMap elements in this document
    :returns: List of full file paths associated with dmdSecGroup
    """
    filesInObjectDirectoryForThisDmdSecGroup = []
    # Get the value of ID for each <dmdSec> and put them in a list,
    # then pass the list into getFileIdsForDmdSec()
    for dmdSec in dmdSecGroup:
        dmdid = dmdSec.get('ID')
        fileIds = getFileIdsForDmdSec(structMaps, dmdid)
        for fileId in fileIds:
            filename = getFptrObjectFilename(fileId, filesInObjectDirectory)
            if filename is not None:
                filesInObjectDirectoryForThisDmdSecGroup.append(filename)
    return filesInObjectDirectoryForThisDmdSecGroup


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


# Generate a 'direct upload' package for a simple item from the Archivematica DIP.
# This package will contain the object file, its thumbnail, a .desc (DC metadata) file,
# and a .full (manifest) file.
def generateSimpleContentDMDirectUploadPackage(dmdSecs, structMaps, dipUuid, outputDipDir, filesInObjectDirectoryForThisDmdSec, filesInThumbnailDirectory):
    dmdSecPair = splitDmdSecs(dmdSecs)
    descFileContents = generateDescFile(dmdSecPair['dc'], dmdSecPair['nonDc'], dipUuid)
    
    # Get the object base filename and extension. Since we are dealing with simple items,
    # there should only be one file in filesInObjectDirectoryForThisDmdSec.
    objectFilePath, objectFileFilename = os.path.split(filesInObjectDirectoryForThisDmdSec[0])
    objectFileBaseFilename, objectFileExtension = os.path.splitext(objectFileFilename)    
    
    # Write the .desc file into the output directory.
    descFile = open(os.path.join(outputDipDir, objectFileBaseFilename + '.desc'), "wb")
    descFile.write(descFileContents)
    descFile.close()
    
    # Copy the object file into the output directory.
    objectFileDest = os.path.join(outputDipDir, objectFileBaseFilename + objectFileExtension)
    shutil.copy(filesInObjectDirectoryForThisDmdSec[0], objectFileDest)

    # Copy the thumbnail into the output directory. The file must end in .icon.
    # The thumbnail filenames in the DIP use the corresponding file's UUID (i.e.,
    # the first 36 characters of the object file's base name).
    thumbnailFilename = objectFileBaseFilename[:36] + '.jpg'
    for thumbnailPath in filesInThumbnailDirectory:
        match = re.search(r'%s$' % thumbnailFilename, thumbnailPath)
        if match:
            shutil.copy(thumbnailPath, os.path.join(outputDipDir, objectFileBaseFilename + '.icon'))

    fullFileContents = generateFullFileEntry(objectFileBaseFilename + objectFileExtension, objectFileBaseFilename, objectFileExtension)
    fullFile = open(os.path.join(outputDipDir, objectFileBaseFilename + '.full'), "wb")
    fullFile.write(fullFileContents)
    fullFile.close()


# Generate a 'direct upload' package for a compound item from the Archivematica DIP.
# Consults the structMap (the Archivematica-generated structMap by default but if there
# is a user-submitted one, that one is transformed to index.cpd via XSL) and write out
# a corresponding structure (index.cpd) file. Also, for every object file, copy the file, 
# create an .icon, create a .desc file, plus create index.desc, index.cpd, index.full,
# and ready.txt.
def generateCompoundContentDMDirectUploadPackage(dmdSecs, structMaps, dipUuid, outputDipDir, filesInObjectDirectoryForThisDmdSecGroup, filesInThumbnailDirectory):
    dmdSecPair = splitDmdSecs(dmdSecs)
    nonDcMetadata = dmdSecPair['nonDc']
    dcMetadata = dmdSecPair['dc']
    descFileContents = generateDescFile(dcMetadata, nonDcMetadata, dipUuid)
    # Null out nonDcMetadataForChildren, since we don't want child-level descriptions.
    # We handle dcMetadata for children below.
    nonDcMetadataForChildren = {}
    nonDcMetadataForChildren['aip_uuid'] = [dipUuid[-36:]]

    # Each item needs to have its own directory under outputDipDir. Since these item-level directories
    # will end up in CONTENTdm's import/cdoc directory, they need to be unique; therefore, we can't use the
    # dmdSec IDs, which are not unique across DIPs. To supply a unique UUID for each compound item, we use
    # the the first eight characters of the UUID of the first file in each compound item.
    firstFilePath, firstFileFilename = os.path.split(filesInObjectDirectoryForThisDmdSecGroup[0])
    itemDirUuid = firstFileFilename[:8]
    outputItemDir = os.path.join(outputDipDir, itemDirUuid)
    if not os.path.exists(outputItemDir):
        os.mkdir(outputItemDir)
    
    # Output a .desc file for the parent item (index.desc).
    descFile = open(os.path.join(outputItemDir, 'index.desc'), "wb")
    descFile.write(descFileContents)
    descFile.close()

    # Start to build the index.cpd file if there is only one structMap;
    # if there are 2 (i.e., there is a user-supplied one), convert it to
    # a .cpd file via XSLT.
    if (len(structMaps)) == 1:
        cpdFileContent = "<cpd>\n  <type>Document</type>\n"
    if (len(structMaps)) == 2:
        # Perform XSLT transform. Serialize the DOM object before passing
        # it to transformUserSuppliedStructMap().
        serializedStructMap = structMaps[1].toxml()
        cpdFileContent = transformUserSuppliedStructMap(serializedStructMap)

    # Start to build the index.full file. This entry is for the index.cpd file.
    titleValues = ''
    if dcMetadata is not None:
        if len(dcMetadata['title']) == 1:
            titleValues += dcMetadata['title'][0]
        # Repeated values in CONTENTdm metadata need to be separated with semicolons.
        if len(dcMetadata['title']) > 1:
            titleValues += '; '.join(dcMetadata['title'])
    fullFileContents = generateFullFileEntry(titleValues, 'index', '.cpd')

    # Archivematica's structMap is always the first one; the user-submitted
    # structMap (if it exists) is always the second one. If the user-submitted
    # structMap is present, parse it for the SIP structure so we can use that
    # structure in the CONTENTdm packages.
    if (len(structMaps)) == 2:
        structMapDom = structMaps[1]
    else:
        structMapDom = structMaps[0]
    structMapDict = parseStructMap(structMapDom, filesInObjectDirectoryForThisDmdSecGroup)

    # Determine the order in which we will add the child-level rows to the .cpd and .full files.
    Orders = []
    for fptr, details in structMapDict.iteritems():
        Orders.append(details['order'])

    # Iterate through the list of order values and add the matching structMapDict entry
    # to the .cpd file (and copy the file into the output directory).
    for order in sorted(Orders):
        for k, v in structMapDict.iteritems():
            # Get each access file's base filesname without extension, since we'll use it
            # for the .icon and .desc files.
            accessFileBasenameName, accessFileBasenameExt = os.path.splitext(v['filename'])
            # The UUID is the first 36-characters of the filename.
            accessFileUuid = accessFileBasenameName[:36]
            # Remove the UUID from the basename.
            accessFileBasenameName = accessFileBasenameName[37:]
            # Reassemble the basename.
            accessFileBasenameName = accessFileBasenameName + '-' + accessFileUuid

            # Get the name of the first file in the sorted order; we use this later to create
            # a thumbnail for current parent item.
            if v['order'] == '00001':
                parentThumbnailFilename = accessFileBasenameName + '.icon' 

            if order == v['order']:
                # Process each object file.
                for fullPath in filesInObjectDirectoryForThisDmdSecGroup:
                    # For each object file, output the object file. We need to find the full path
                    # of the file identified in v['filename'].
                    if (v['filename'] in fullPath):
                        shutil.copy(fullPath, os.path.join(outputItemDir, accessFileBasenameName + accessFileBasenameExt))

                    # For each object file, copy the thumbnail in the DIP to the import package.
                    # The file must have the same name as the object file but it must end in .icon.
                    for thumbnailFilePath in filesInThumbnailDirectory:
                        thumbnailBasename = os.path.basename(thumbnailFilePath)
                        # Strip off thumbnail extension so we can match on the name.
                        thumbnailBasenameName, thumbnailBasenameext = os.path.splitext(thumbnailBasename)
                        if (thumbnailBasenameName in v['filename']):
                            thumbnailFilename = accessFileBasenameName + '.icon'
                            shutil.copy(thumbnailFilePath, os.path.join(outputItemDir, thumbnailFilename))

                # For each child object file, output a .desc file. Currently, we do not
                # support child-level descriptions other than title, so we use the filename
                # as the title if there isn't a user-supplied csv or structMap to provide 
                # labels as per https://www.archivematica.org/wiki/CONTENTdm_integration.
                childFileLabel = accessFileBasenameName
                dcMetadata = parseDmdSec(None, childFileLabel)
                nonDcMetadataForChildren['title'] = [childFileLabel]
                descFileContents = generateDescFile(dcMetadata, nonDcMetadataForChildren)
                descFilename = accessFileBasenameName + '.desc'
                descFile = open(os.path.join(outputItemDir, descFilename), "wb")
                descFile.write(descFileContents)
                descFile.close()

                # For each object file, add its .full file values. These entries do not
                # have anything in their <title> elements.
                fullFileContents += generateFullFileEntry('', accessFileBasenameName, accessFileBasenameExt)
                
                if (len(structMaps)) == 1:
                    # For each object file, add its .cpd file values. 
                    cpdFileContent += "  <page>\n"
                    cpdFileContent += "    <pagetitle>" + childFileLabel + "</pagetitle>\n"
                    cpdFileContent += "    <pagefile>" + accessFileBasenameName + accessFileBasenameExt + "</pagefile>\n"
                    cpdFileContent += "    <pageptr>+</pageptr>\n"
                    cpdFileContent += "  </page>\n"

    # Write out the index.full file. 
    fullFile = open(os.path.join(outputItemDir, 'index.full'), "wb")
    fullFile.write(fullFileContents)
    fullFile.close()

    # If we're generating an index.cpd file (as opposed to using XSL on a
    # user-submitted one), finish adding the content.
    if (len(structMaps)) == 1:
        cpdFileContent += '</cpd>'
        
    # Write out the index.cpd file.        
    indexCpdFile = open(os.path.join(outputItemDir, 'index.cpd'), "wb")
    indexCpdFile.write(cpdFileContent)
    indexCpdFile.close()

    # Create a thumbnail for the parent item (index.icon), using the icon from the first item
    # in the METS file. parentThumbnailFilename
    shutil.copy(os.path.join(outputItemDir, parentThumbnailFilename), os.path.join(outputItemDir, 'index.icon'))

    # Write out the ready.txt file which contains the string '1'.
    readyFile = open(os.path.join(outputItemDir, 'ready.txt'), "wb")
    readyFile.write('1')
    readyFile.close()


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
            # If first time through, write out header
            if not csv_header_ref:
                csv_header_ref = csv_header
                writer.writerow(csv_header_ref)
                print('Tabfile header:', csv_header)
            # Write csv_row
            writer.writerow(csv_values)
            print('Values:', csv_values)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='restructure')
    # FIXME make --uuid param actually the UUID not the name
    parser.add_argument('--uuid', action="store", dest='uuid', metavar='UUID', help='SIP-UUID')
    parser.add_argument('--dipDir', action="store", dest='dipDir', metavar='dipDir', help='DIP Directory')
    parser.add_argument('--server', action="store", dest='contentdmServer', metavar='server', help='Target CONTENTdm server')
    parser.add_argument('--collection', action="store", dest='targetCollection',
                        metavar='targetCollection', help='Target CONTENTdm Collection')
    parser.add_argument('--ingestFormat', action="store", dest='ingestFormat', metavar='ingestFormat', choices=('directupload', 'projectclient'),
                        default='directupload', help='The format of the ingest package, either directupload or projectclient')
    parser.add_argument('--outputDir', action="store", dest='outputDir', metavar='outputDir',
                        help='The destination for the restructured DIPs')

    args = parser.parse_args()
    # FIXME move more of this to a main function - only parse the args in the if __name__==__main__

    # Define the directory where DIPs are waiting to be processed.
    inputDipDir = args.dipDir
    
    # Use %watchDirectoryPath%uploadedDIPs as the output directory for the directupload and 
    # projectclient output. Also create a 'CONTENTdm' subdirectory for DIPs created by this microservice.
    outputDipDir = prepareOutputDir(args.outputDir, args.ingestFormat, args.uuid)

    # Perform some preliminary validation on the argument values.
    if not os.path.isdir(inputDipDir):
        print("Can't find", inputDipDir, ', exiting.')
        sys.exit(1)

    # Read and parse the METS file.
    metsFile = os.path.join(inputDipDir, 'METS.' + args.uuid[-36:] + '.xml')
    root = etree.parse(metsFile)

    # Get the structMaps so we can pass them into the DIP creation functions.
    structMaps = root.findall('mets:structMap', namespaces=ns.NSMAP)

    # If there is a user-submitted structMap (i.e., len(structMapts) is 2,
    # use that one.
    # QUESTION why not use physical structMap always?
    archivematica_structmap = structMaps[0]
    if len(structMaps) == 2:
        itemCountType = getItemCountType(structMaps[1])
    else:
        itemCountType = getItemCountType(archivematica_structmap)

    # Populate lists of files in the DIP objects and thumbnails directories.
    # QUESTION why not use the same function for both of these and filter for .jpg?
    filesInObjectDirectory = getObjectDirectoryFiles(os.path.join(inputDipDir, 'objects'))
    filesInThumbnailDirectory = glob.glob(os.path.join(inputDipDir, 'thumbnails', "*.jpg"))
    
    # Get the dmdSec nodes from the METS file.
    dmdSecs = root.findall('mets:dmdSec', namespaces=ns.NSMAP)
    numDmdSecs = len(dmdSecs)
    # Group the dmdSecs into item-specific pairs (for DC and OTHER; both types are optional).
    groupedDmdSecs = groupDmdSecs(dmdSecs, archivematica_structmap)

    if args.ingestFormat == 'projectclient':
        dmdsecs = {e.get('ID'): e for e in dmdSecs}
        generate_project_client_package(outputDipDir, itemCountType, archivematica_structmap, dmdsecs, args.uuid[-36:])
        sys.exit(0)

    # Bulk DIP. Assumes that a single item (i.e. no bulk) will only have one
    # dmdSec, (i.e., not "dmdSec_1 dmdSec_2"). This is probably a safe assumption
    # because a single item's metadata would either come from a dublincore.xml
    # file or from the metadata entry form in the Dashboard. Only edge case
    # would be if the metadata was from a single-row metadata.csv file that had 
    # a combination of dcterms and custom metadata.
    if numDmdSecs > 1:
        # For simple items.  
        if 'simple' in itemCountType:
            for dmdSecGroup in groupedDmdSecs:                
                filesInObjectDirectoryForThisDmdSecGroup = getFilesInObjectDirectoryForThisDmdSecGroup(dmdSecGroup, structMaps)
                if args.ingestFormat == 'directupload':
                    generateSimpleContentDMDirectUploadPackage(dmdSecGroup, structMaps, args.uuid, outputDipDir, filesInObjectDirectoryForThisDmdSecGroup, filesInThumbnailDirectory)

        # For compound items.
        if 'compound' in itemCountType:
            for dmdSecGroup in groupedDmdSecs:
                filesInObjectDirectoryForThisDmdSecGroup = getFilesInObjectDirectoryForThisDmdSecGroup(dmdSecGroup, structMaps)
                if args.ingestFormat == 'directupload':
                    generateCompoundContentDMDirectUploadPackage(dmdSecGroup, structMaps,  args.uuid, outputDipDir, filesInObjectDirectoryForThisDmdSecGroup, filesInThumbnailDirectory)

    # 0 or 1 dmdSec (single-item DIP).
    else:
        # For simple items.
        if len(filesInObjectDirectory) <= 1 and args.ingestFormat == 'directupload':
            generateSimpleContentDMDirectUploadPackage(dmdSecs, structMaps, args.uuid, outputDipDir, filesInObjectDirectory, filesInThumbnailDirectory)

        # For compound items.
        if len(filesInObjectDirectory) > 1 and args.ingestFormat == 'directupload':
            generateCompoundContentDMDirectUploadPackage(dmdSecs, structMaps, args.uuid, outputDipDir, filesInObjectDirectory, filesInThumbnailDirectory)
