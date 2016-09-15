#!/usr/bin/env python2
# -*- coding: utf-8 -*-
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

from __future__ import print_function
import collections
import copy
from glob import glob
import lxml.etree as etree
import os
import re
import sys
import traceback
from uuid import uuid4

import django
django.setup()
# dashboard
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Agent, Derivation, DublinCore, Event, File, FileID, FPCommandOutput, SIP, SIPArrange, Transfer

import archivematicaCreateMETSReingest
from createMETSDataverse import create_dataverse_sip_dmdsec, create_dataverse_tabfile_dmdsec
from archivematicaCreateMETSMetadataCSV import parseMetadata
from archivematicaCreateMETSRights import archivematicaGetRights
from archivematicaCreateMETSRightsDspaceMDRef import archivematicaCreateMETSRightsDspaceMDRef
from archivematicaCreateMETSTrim import getTrimDmdSec
from archivematicaCreateMETSTrim import getTrimFileDmdSec
from archivematicaCreateMETSTrim import getTrimAmdSec
from archivematicaCreateMETSTrim import getTrimFileAmdSec
# archivematicaCommon
from archivematicaFunctions import escape
from archivematicaFunctions import strToUnicode
from archivematicaFunctions import normalizeNonDcElementName
from custom_handlers import get_script_logger
import namespaces as ns
from sharedVariablesAcrossModules import sharedVariablesAcrossModules
sharedVariablesAcrossModules.globalErrorCount = 0

from bagit import Bag, BagError

#Global Variables

globalFileGrps = {}
globalFileGrpsUses = ["original", "submissionDocumentation", "preservation", "service", "access", "license", "text/ocr", "metadata", "derivative"]
for use in globalFileGrpsUses:
    grp = etree.Element(ns.metsBNS + "fileGrp")
    grp.set("USE", use)
    globalFileGrps[use] = grp

##counters
global amdSecs
amdSecs = []
global dmdSecs
dmdSecs = []
global globalDmdSecCounter
globalDmdSecCounter = 0
global globalAmdSecCounter
globalAmdSecCounter = 0
global globalTechMDCounter
globalTechMDCounter = 0
global globalRightsMDCounter
globalRightsMDCounter = 0
global globalDigiprovMDCounter
globalDigiprovMDCounter = 0
global fileNameToFileID #Used for mapping structMaps included with transfer
fileNameToFileID = {}

global trimStructMap
trimStructMap = None
global trimStructMapObjects
trimStructMapObjects = None
#GROUPID="G1" -> GROUPID="Group-%object's UUID%"
##group of the object and it's related access, license

CSV_METADATA = {}

#move to common
def newChild(parent, tag, text=None, tailText=None, sets=[]):
    # TODO convert sets to a dict, and use **dict
    child = etree.SubElement(parent, tag)
    child.text = strToUnicode(text)
    if tailText:
        child.tail = strToUnicode(tailText)
    for set in sets:
        key, value = set
        child.set(key, value)
    return child



SIPMetadataAppliesToType = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'
TransferMetadataAppliesToType = '45696327-44c5-4e78-849b-e027a189bf4d'
FileMetadataAppliesToType = '7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17'


def getDublinCore(unit, id):
    db_field_mapping = collections.OrderedDict([
        ("title", "title"),
        ("creator", "creator"),
        ("subject", "subject"),
        ("description", "description"),
        ("publisher", "publisher"),
        ("contributor", "contributor"),
        ("date", "date"),
        ("type", "type"),
        ("format", "format"),
        ("identifier", "identifier"),
        ("source", "source"),
        ("relation", "relation"),
        ("language", "language"),
        ("coverage", "coverage"),
        ("rights", "rights"),
        ("is_part_of", "isPartOf"),
    ])

    try:
        dc = DublinCore.objects.get(metadataappliestotype_id=unit,
                                    metadataappliestoidentifier=id)
    except DublinCore.DoesNotExist:
        return

    ret = etree.Element(ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, 'dc': ns.dcNS})
    ret.set(ns.xsiBNS + "schemaLocation", ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")

    for dbname, term in db_field_mapping.items():
        txt = getattr(dc, dbname)
        elem_ns = ''
        # See http://dublincore.org/documents/2012/06/14/dcmi-terms/?v=elements for which elements are which namespace
        if term in ('contributor', 'coverage', 'creator', 'date', 'description', 'format', 'identifier', 'language', 'publisher', 'relation', 'rights', 'source', 'subject', 'title', 'type'):
            elem_ns = ns.dcBNS
        elif term in ('isPartOf',):
            elem_ns = ns.dctermsBNS
        if txt:
            newChild(ret, elem_ns + term, text=txt)
    return ret


def createDMDIDsFromCSVMetadata(path):
    """
    Creates dmdSecs with metadata associated with path from the metadata.csv

    :param path: Path relative to the SIP to find CSV metadata on
    :return: Space-separated list of DMDIDs or empty string
    """
    metadata = CSV_METADATA.get(path, {})
    dmdsecs = createDmdSecsFromCSVParsedMetadata(metadata)
    return ' '.join([d.get('ID') for d in dmdsecs])


def createDmdSecsFromCSVParsedMetadata(metadata):
    """
    Create dmdSec(s) from the provided metadata.

    :param metadata: OrderedDict with the metadata keys and a list of values
    :return: List of dmdSec Elements created
    """
    global globalDmdSecCounter
    global dmdSecs
    dc = None
    other = None
    ret = []

    # Archivematica does not support refined Dublin Core, e.g.
    # multitiered terms in the format dc.description.abstract
    # If these terms are encountered, an element with only the
    # last portion of the name will be added.
    # e.g., dc.description.abstract is mapped to <dc:abstract>
    refinement_regex = re.compile('\w+\.(.+)')

    for key, value in metadata.items():
        if key.startswith("dc.") or key.startswith("dcterms."):
            if dc is None:
                globalDmdSecCounter += 1
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                dmdSec = etree.Element(ns.metsBNS + "dmdSec", ID=ID)
                dmdSecs.append(dmdSec)
                ret.append(dmdSec)
                mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
                mdWrap.set("MDTYPE", "DC")
                xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
                dc = etree.Element(ns.dctermsBNS + "dublincore", nsmap={"dcterms": ns.dctermsNS, 'dc': ns.dcNS})
                dc.set(ns.xsiBNS + "schemaLocation", ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
                xmlData.append(dc)
            elem_namespace = ""
            if key.startswith("dc."):
                key = key.replace("dc.", "", 1)
                elem_namespace = ns.dcBNS
            elif key.startswith("dcterms."):
                key = key.replace("dcterms.", "", 1)
                elem_namespace = ns.dctermsBNS
            match = re.match(refinement_regex, key)
            if match:
                key, = match.groups()
            for v in value:
                try:
                    etree.SubElement(dc, elem_namespace + key).text = v.decode('utf-8')
                except UnicodeDecodeError:
                    print("Skipping DC value; not valid UTF-8: {}".format(v), file=sys.stderr)
        else:  # not a dublin core item
            if other is None:
                globalDmdSecCounter += 1
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                dmdSec = etree.Element(ns.metsBNS + "dmdSec", ID=ID)
                dmdSecs.append(dmdSec)
                ret.append(dmdSec)
                mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
                mdWrap.set("MDTYPE", "OTHER")
                mdWrap.set("OTHERMDTYPE", "CUSTOM")
                other = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
            for v in value:
                try:
                    etree.SubElement(other, normalizeNonDcElementName(key)).text = v.decode('utf-8')
                except UnicodeDecodeError:
                    print("Skipping DC value; not valid UTF-8: {}".format(v), file=sys.stderr)
    return ret


def createDublincoreDMDSecFromDBData(unit_type, unit_uuid, baseDirectoryPath):
    """
    Creates dmdSec containing DublinCore metadata for unit_uuid.

    If DC metadata exists in the DB, use that.
    If not, check the transfer metadata directory for a dublincore.xml file, and use that.

    :param str unit_type: Pk from MetadataAppliesToType
    :param str unit_uuid: SIP UUID
    :param str baseDirectoryPath: SIP path to check for transfer metadata
    :return: Tuple of (dmdSec Element, DMDID), or None
    """
    dc = getDublinCore(unit_type, unit_uuid)
    if dc is None:
        transfers = os.path.join(baseDirectoryPath, "objects/metadata/transfers/")
        if not os.path.isdir(transfers):
            return None
        for transfer in os.listdir(transfers):
            dcXMLFile = os.path.join(transfers, transfer, "dublincore.xml")
            if os.path.isfile(dcXMLFile):
                try:
                    parser = etree.XMLParser(remove_blank_text=True)
                    dtree = etree.parse(dcXMLFile, parser)
                    dc = dtree.getroot()
                    break
                except Exception as inst:
                    print("error parsing file:", dcXMLFile, file=sys.stderr)
                    print(type(inst), file=sys.stderr)     # the exception instance
                    print(inst.args, file=sys.stderr)
                    traceback.print_exc(file=sys.stdout)
                    sharedVariablesAcrossModules.globalErrorCount += 1
        else:  # break not called, no DC successfully parsed
            return None
    global globalDmdSecCounter
    globalDmdSecCounter += 1
    dmdSec = etree.Element(ns.metsBNS + "dmdSec")
    ID = "dmdSec_" + globalDmdSecCounter.__str__()
    dmdSec.set("ID", ID)
    mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    xmlData.append(dc)
    return (dmdSec, ID)

def createDSpaceDMDSec(label, dspace_mets_path, directoryPathSTR):
    """
    Parse DSpace METS file and create a dmdSecs from the info.

    One dmdSec will contain a mdRef to the DSpace METS file. The other dmdSec
    will contain Dublin Core metadata with the identifier and parent collection
    identifier.

    :param str label: LABEL for the mdRef
    :param str dspace_mets_path: Path to the DSpace METS
    :param str directoryPathSTR: Relative path to the DSpace METS
    :return: dict of {<dmdSec ID>: <dmdSec Element>}
    """
    global globalDmdSecCounter
    dmdsecs = collections.OrderedDict()
    root = etree.parse(dspace_mets_path)

    # Create mdRef to DSpace METS file
    globalDmdSecCounter += 1
    dmdid = "dmdSec_" + str(globalDmdSecCounter)
    dmdsec = etree.Element(ns.metsBNS + "dmdSec", ID=dmdid)
    dmdsecs[dmdid] = dmdsec
    xptr_dmdids = [i.get('ID') for i in root.findall("{http://www.loc.gov/METS/}dmdSec")]
    try:
        xptr = "xpointer(id('{}'))".format(' '.join(xptr_dmdids))
    except TypeError:  # Trying to .join() on a list with None
        print('dmdSec in', dspace_mets_path, 'missing an ID', file=sys.stderr)
        raise
    newChild(dmdsec, ns.metsBNS + "mdRef", text=None, sets=[("LABEL", label), (ns.xlinkBNS + "href", directoryPathSTR), ("MDTYPE", "OTHER"), ("LOCTYPE", "OTHER"), ("OTHERLOCTYPE", "SYSTEM"), ("XPTR", xptr)])

    # Create dmdSec with DC identifier and isPartOf
    identifier = root.findtext('mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@qualifier="uri"]', namespaces=ns.NSMAP)
    part_of = root.findtext('mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@qualifier="isPartOf"]', namespaces=ns.NSMAP)
    if identifier is None or part_of is None:
        print('Unable to parse identifer and isPartOf from', dspace_mets_path, file=sys.stderr)
        return {}
    metadata = {
        'dc.identifier': [identifier],
        'dcterms.isPartOf': [part_of],
    }
    dc_dmdsecs = createDmdSecsFromCSVParsedMetadata(metadata)
    dmdsec = dc_dmdsecs[0]  # Should only be one dmdSec
    dmdid = dmdsec.get('ID')
    dmdsecs[dmdid] = dmdsec

    return dmdsecs


def createTechMD(fileUUID):
    ret = etree.Element(ns.metsBNS + "techMD")
    techMD = ret

    global globalTechMDCounter
    globalTechMDCounter += 1
    techMD.set("ID", "techMD_"+ globalTechMDCounter.__str__())

    mdWrap = etree.SubElement(techMD, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "PREMIS:OBJECT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")

    f = File.objects.get(uuid=fileUUID)
    fileSize = str(f.size)

    #OBJECT
    object = etree.SubElement(xmlData, ns.premisBNS + "object", nsmap={'premis': ns.premisNS})
    object.set(ns.xsiBNS+"type", "premis:file")
    object.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    object.set("version", "2.2")

    objectIdentifier = etree.SubElement(object, ns.premisBNS + "objectIdentifier")
    etree.SubElement(objectIdentifier, ns.premisBNS + "objectIdentifierType").text = "UUID"
    etree.SubElement(objectIdentifier, ns.premisBNS + "objectIdentifierValue").text = fileUUID

    objectCharacteristics = etree.SubElement(object, ns.premisBNS + "objectCharacteristics")
    etree.SubElement(objectCharacteristics, ns.premisBNS + "compositionLevel").text = "0"

    fixity = etree.SubElement(objectCharacteristics, ns.premisBNS + "fixity")
    etree.SubElement(fixity, ns.premisBNS + "messageDigestAlgorithm").text = f.checksumtype
    etree.SubElement(fixity, ns.premisBNS + "messageDigest").text = f.checksum

    etree.SubElement(objectCharacteristics, ns.premisBNS + "size").text = fileSize

    files = FileID.objects.filter(file_id=fileUUID)
    if not files.exists():
        format = etree.SubElement(objectCharacteristics, ns.premisBNS + "format")
        formatDesignation = etree.SubElement(format, ns.premisBNS + "formatDesignation")
        etree.SubElement(formatDesignation, ns.premisBNS + "formatName").text = "Unknown"
    for row in files.values_list('format_name', 'format_version', 'format_registry_name', 'format_registry_key'):
        #print row
        format = etree.SubElement(objectCharacteristics, ns.premisBNS + "format")

        formatDesignation = etree.SubElement(format, ns.premisBNS + "formatDesignation")
        etree.SubElement(formatDesignation, ns.premisBNS + "formatName").text = row[0]
        etree.SubElement(formatDesignation, ns.premisBNS + "formatVersion").text = row[1]

        formatRegistry = etree.SubElement(format, ns.premisBNS + "formatRegistry")
        etree.SubElement(formatRegistry, ns.premisBNS + "formatRegistryName").text = row[2]
        etree.SubElement(formatRegistry, ns.premisBNS + "formatRegistryKey").text = row[3]

    objectCharacteristicsExtension = etree.SubElement(objectCharacteristics, ns.premisBNS + "objectCharacteristicsExtension")

    parser = etree.XMLParser(remove_blank_text=True)
    documents = FPCommandOutput.objects.filter(file_id=fileUUID, rule__purpose__in=['characterization', 'default_characterization']).values_list('content')
    for document, in documents:
        # This needs to be converted into an str because lxml doesn't accept
        # XML documents in unicode strings if the document contains an
        # encoding declaration.
        output = etree.XML(document.encode("utf-8"), parser)
        objectCharacteristicsExtension.append(output)

    try:
        f = File.objects.get(uuid=fileUUID)
    except File.DoesNotExist:
        print("Error: no location found.", file=sys.stderr)
    else:
        etree.SubElement(object, ns.premisBNS + "originalName").text = escape(f.originallocation)

    # Derivations
    derivations = Derivation.objects.filter(source_file_id=fileUUID, event__isnull=False)
    for derivation in derivations:
        relationship = etree.SubElement(object, ns.premisBNS + "relationship")
        etree.SubElement(relationship, ns.premisBNS + "relationshipType").text = "derivation"
        etree.SubElement(relationship, ns.premisBNS + "relationshipSubType").text = "is source of"

        relatedObjectIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierValue").text = derivation.derived_file_id

        relatedEventIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierValue").text = derivation.event_id

    derivations = Derivation.objects.filter(derived_file_id=fileUUID, event__isnull=False)
    for derivation in derivations:
        relationship = etree.SubElement(object, ns.premisBNS + "relationship")
        etree.SubElement(relationship, ns.premisBNS + "relationshipType").text = "derivation"
        etree.SubElement(relationship, ns.premisBNS + "relationshipSubType").text = "has source"

        relatedObjectIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierValue").text = derivation.source_file_id

        relatedEventIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierValue").text = derivation.event_id

    return ret

def createDigiprovMD(fileUUID):
    """
    Create digiprovMD for PREMIS Events and linking Agents.
    """
    global globalDigiprovMDCounter
    ret = []

    events = Event.objects.filter(file_uuid_id=fileUUID)
    for event_record in events:
        globalDigiprovMDCounter += 1
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD", ID='digiprovMD_' + str(globalDigiprovMDCounter))
        ret.append(digiprovMD)

        createEvent(digiprovMD, event_record)

    agents = Agent.objects.filter(event__file_uuid_id=fileUUID).distinct()
    for agent in agents:
        globalDigiprovMDCounter += 1
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD", ID='digiprovMD_' + str(globalDigiprovMDCounter))
        ret.append(digiprovMD)

        createAgent(digiprovMD, agent)

    return ret

def createEvent(digiprovMD, event_record):
    """ Create a PREMIS Event as a SubElement of digiprovMD. """
    mdWrap = etree.SubElement(digiprovMD, ns.metsBNS + "mdWrap", MDTYPE="PREMIS:EVENT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    event = etree.SubElement(xmlData, ns.premisBNS + "event", nsmap={'premis': ns.premisNS})
    event.set(ns.xsiBNS + "schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    event.set("version", "2.2")

    eventIdentifier = etree.SubElement(event, ns.premisBNS + "eventIdentifier")
    etree.SubElement(eventIdentifier, ns.premisBNS + "eventIdentifierType").text = "UUID"
    etree.SubElement(eventIdentifier, ns.premisBNS + "eventIdentifierValue").text = event_record.event_id

    etree.SubElement(event, ns.premisBNS + "eventType").text = event_record.event_type
    etree.SubElement(event, ns.premisBNS + "eventDateTime").text = event_record.event_datetime.isoformat()
    etree.SubElement(event, ns.premisBNS + "eventDetail").text = escape(event_record.event_detail)

    eventOutcomeInformation = etree.SubElement(event, ns.premisBNS + "eventOutcomeInformation")
    etree.SubElement(eventOutcomeInformation, ns.premisBNS + "eventOutcome").text = event_record.event_outcome
    eventOutcomeDetail = etree.SubElement(eventOutcomeInformation, ns.premisBNS + "eventOutcomeDetail")
    etree.SubElement(eventOutcomeDetail, ns.premisBNS + "eventOutcomeDetailNote").text = escape(event_record.event_outcome_detail)

    # linkingAgentIdentifier
    for agent in event_record.agents.all():
        linkingAgentIdentifier = etree.SubElement(event, ns.premisBNS + "linkingAgentIdentifier")
        etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierType").text = agent.identifiertype
        etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierValue").text = agent.identifiervalue

def createAgent(digiprovMD, agent_record):
    """ Creates a PREMIS Agent as a SubElement of digiprovMD. """
    mdWrap = etree.SubElement(digiprovMD, ns.metsBNS + "mdWrap", MDTYPE="PREMIS:AGENT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    agent = etree.SubElement(xmlData, ns.premisBNS + "agent", nsmap={'premis': ns.premisNS})
    agent.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    agent.set("version", "2.2")

    agentIdentifier = etree.SubElement(agent, ns.premisBNS + "agentIdentifier")
    etree.SubElement(agentIdentifier, ns.premisBNS + "agentIdentifierType").text = agent_record.identifiertype
    etree.SubElement(agentIdentifier, ns.premisBNS + "agentIdentifierValue").text = agent_record.identifiervalue
    etree.SubElement(agent, ns.premisBNS + "agentName").text = agent_record.name
    etree.SubElement(agent, ns.premisBNS + "agentType").text = agent_record.agenttype


def getAMDSec(fileUUID, filePath, use, type, id, transferUUID, itemdirectoryPath, typeOfTransfer, baseDirectoryPath):
    global globalAmdSecCounter
    global globalRightsMDCounter
    global globalDigiprovMDCounter
    globalAmdSecCounter += 1
    AMDID = "amdSec_%s" % (globalAmdSecCounter.__str__())
    AMD = etree.Element(ns.metsBNS + "amdSec")
    AMD.set("ID", AMDID)
    ret = (AMD, AMDID)
    #tech MD
    #digiprob MD
    AMD.append(createTechMD(fileUUID))

    if use == "original":
        metadataAppliesToList = [(fileUUID, FileMetadataAppliesToType), (id, SIPMetadataAppliesToType), (transferUUID, TransferMetadataAppliesToType)]
        for a in archivematicaGetRights(metadataAppliesToList, fileUUID):
            globalRightsMDCounter +=1
            rightsMD = etree.SubElement(AMD, ns.metsBNS + "rightsMD")
            rightsMD.set("ID", "rightsMD_" + globalRightsMDCounter.__str__())
            mdWrap = newChild(rightsMD, ns.metsBNS + "mdWrap")
            mdWrap.set("MDTYPE", "PREMIS:RIGHTS")
            xmlData = newChild(mdWrap, ns.metsBNS + "xmlData")
            xmlData.append(a)

        if typeOfTransfer == "Dspace":
            for a in archivematicaCreateMETSRightsDspaceMDRef(fileUUID, filePath, transferUUID, itemdirectoryPath):
                globalRightsMDCounter +=1
                rightsMD = etree.SubElement(AMD, ns.metsBNS + "rightsMD")
                rightsMD.set("ID", "rightsMD_" + globalRightsMDCounter.__str__())
                rightsMD.append(a)

        elif typeOfTransfer == "TRIM":
            digiprovMD = getTrimFileAmdSec(baseDirectoryPath, id, fileUUID)
            globalDigiprovMDCounter += 1
            digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
            AMD.append(digiprovMD)

    for a in createDigiprovMD(fileUUID):
        AMD.append(a)

    return ret

def getIncludedStructMap(baseDirectoryPath):
    global fileNameToFileID
    global trimStructMap
    global trimStructMapObjects

    ret = []
    transferMetadata = os.path.join(baseDirectoryPath, "objects/metadata/transfers")
    if not os.path.isdir(transferMetadata):
        return []
    baseLocations = os.listdir(transferMetadata)
    baseLocations.append(baseDirectoryPath)
    for dir in baseLocations:
        dirPath = os.path.join(transferMetadata, dir)
        structMapXmlPath = os.path.join(dirPath, "mets_structmap.xml")
        if not os.path.isdir(dirPath):
            continue
        if os.path.isfile(structMapXmlPath):
            tree = etree.parse(structMapXmlPath)
            root = tree.getroot() #TDOD - not root to return, but sub element structMap
            #print etree.tostring(root)
            structMap = root.find(ns.metsBNS + "structMap")
            id = structMap.get("ID")
            if not id:
                structMap.set("ID", "structMap_2")
            ret.append(structMap)
            for item in structMap.findall(".//" + ns.metsBNS + "fptr"):
                fileName = item.get("FILEID")
                if fileName in fileNameToFileID:
                    #print fileName, " -> ", fileNameToFileID[fileName]
                    item.set("FILEID", fileNameToFileID[fileName])
                else:
                    print("error: no fileUUID for ", fileName, file=sys.stderr)
                    sharedVariablesAcrossModules.globalErrorCount += 1
    for fileName, fileID in  fileNameToFileID.items():
        #locate file based on key
        continue
        print(fileName)
    if trimStructMap != None:
        ret.append(trimStructMap)
    return ret

#DMDID="dmdSec_01" for an object goes in here
#<file ID="file1-UUID" GROUPID="G1" DMDID="dmdSec_02" ADMID="amdSec_01">
def createFileSec(directoryPath, parentDiv, baseDirectoryPath, baseDirectoryName, fileGroupIdentifier, fileGroupType, includeAmdSec=True):
    """
    Creates fileSec and structMap entries for files on disk recursively.

    :param directoryPath: Path to recursively traverse and create METS entries for
    :param parentDiv: structMap div to attach created children to
    :param baseDirectoryPath: SIP path
    :param baseDirectoryName: Name of the %var% for the SIP path
    :param fileGroupIdentifier: SIP UUID
    :param fileGroupType: Name of the foreign key field linking to SIP UUID in files.
    :param includeAmdSec: If True, creates amdSecs for the files
    """
    global fileNameToFileID
    global trimStructMap
    global trimStructMapObjects
    global globalDmdSecCounter
    global globalAmdSecCounter
    global globalDigiprovMDCounter
    global dmdSecs
    global amdSecs

    filesInThisDirectory = []
    dspaceMetsDMDID = None
    try:
        directoryContents = sorted(os.listdir(directoryPath))
    except os.error:
        # Directory doesn't exist
        print(directoryPath, "doesn't exist", file=sys.stderr)
        return

    structMapDiv = etree.SubElement(parentDiv, ns.metsBNS + 'div', TYPE='Directory', LABEL=os.path.basename(directoryPath))

    DMDIDS = createDMDIDsFromCSVMetadata(directoryPath.replace(baseDirectoryPath, "", 1))
    if DMDIDS:
        structMapDiv.set("DMDID", DMDIDS)

    for item in directoryContents:
        itemdirectoryPath = os.path.join(directoryPath, item)
        if os.path.isdir(itemdirectoryPath):
            createFileSec(itemdirectoryPath, structMapDiv, baseDirectoryPath, baseDirectoryName, fileGroupIdentifier, fileGroupType, includeAmdSec)
        elif os.path.isfile(itemdirectoryPath):
            # Setup variables for creating file metadata
            DMDIDS = ""
            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, baseDirectoryName, 1)

            kwargs = {
                "removedtime__isnull": True,
                fileGroupType: fileGroupIdentifier,
                "currentlocation": directoryPathSTR
            }
            try:
                f = File.objects.get(**kwargs)
            except File.DoesNotExist:
                print("No uuid for file: \"", directoryPathSTR, "\"", file=sys.stderr)
                sharedVariablesAcrossModules.globalErrorCount += 1
                continue

            use = f.filegrpuse
            label = f.label
            typeOfTransfer = f.transfer.type if f.transfer else None

            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, "", 1)

            # Special TRIM processing
            if typeOfTransfer == "TRIM" and trimStructMap is None:
                trimStructMap = etree.Element(ns.metsBNS + "structMap", attrib={"TYPE": "logical", "ID": "structMap_2", "LABEL": "Hierarchical arrangement"})
                trimStructMapObjects = etree.SubElement(trimStructMap, ns.metsBNS + "div", attrib={"TYPE": "File", "LABEL": "objects"})

                trimDmdSec = getTrimDmdSec(baseDirectoryPath, fileGroupIdentifier)
                globalDmdSecCounter += 1
                dmdSecs.append(trimDmdSec)
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                trimDmdSec.set("ID", ID)
                trimStructMapObjects.set("DMDID", ID)

                trimAmdSec = etree.Element(ns.metsBNS + "amdSec")
                globalAmdSecCounter += 1
                amdSecs.append(trimAmdSec)
                ID = "amdSec_" + globalAmdSecCounter.__str__()
                trimAmdSec.set("ID", ID)

                digiprovMD = getTrimAmdSec(baseDirectoryPath, fileGroupIdentifier)
                globalDigiprovMDCounter += 1
                digiprovMD.set("ID", "digiprovMD_" + str(globalDigiprovMDCounter))

                trimAmdSec.append(digiprovMD)

                trimStructMapObjects.set("ADMID", ID)

            # Create <div TYPE="Item"> and child <fptr>
            # <fptr FILEID="file-<UUID>" LABEL="filename.ext">
            fileId = "file-{}".format(f.uuid)
            label = item if not label else label
            fileDiv = etree.SubElement(structMapDiv, ns.metsBNS + "div", LABEL=label, TYPE='Item')
            etree.SubElement(fileDiv, ns.metsBNS + 'fptr', FILEID=fileId)
            fileNameToFileID[item] = fileId

            # Determine fileGrp @GROUPID based on the file's fileGrpUse and transfer type
            GROUPID = ""
            if f.filegrpuuid:
                # GROUPID was determined elsewhere
                GROUPID = "Group-%s" % (f.filegrpuuid)
                if use == "TRIM file metadata":
                    use = "metadata"

            elif use in ("original", "submissionDocumentation", "metadata", "maildirFile"):
                # These files are in a group defined by themselves
                GROUPID = "Group-%s" % (f.uuid)
                if use == "maildirFile":
                    use = "original"
                # Check for CSV-based Dublincore dmdSec
                if use == "original":
                    DMDIDS = createDMDIDsFromCSVMetadata(f.originallocation.replace('%transferDirectory%', "", 1))
                    if DMDIDS:
                        fileDiv.set("DMDID", DMDIDS)
                    # More special TRIM processing
                    if typeOfTransfer == "TRIM":
                        trimFileDiv = etree.SubElement(trimStructMapObjects, ns.metsBNS + "div", attrib={"TYPE": "Item"})

                        trimFileDmdSec = getTrimFileDmdSec(baseDirectoryPath, fileGroupIdentifier, f.uuid)
                        globalDmdSecCounter += 1
                        dmdSecs.append(trimFileDmdSec)
                        ID = "dmdSec_" + globalDmdSecCounter.__str__()
                        trimFileDmdSec.set("ID", ID)

                        trimFileDiv.set("DMDID", ID)

                        etree.SubElement(trimFileDiv, ns.metsBNS + "fptr", FILEID=fileId)

            elif typeOfTransfer == "Dspace" and (use in ("license", "text/ocr", "DSPACEMETS")):
                # Dspace transfers are treated specially, but some of these fileGrpUses may be encountered in other types
                kwargs = {
                    "removedtime__isnull": True,
                    fileGroupType: fileGroupIdentifier,
                    "filegrpuse": "original",
                    "originallocation__startswith": os.path.dirname(f.originallocation)
                }
                try:
                    original_file = File.objects.get(**kwargs)
                    GROUPID = 'Group-' + original_file.uuid
                except (File.DoesNotExist, File.MultipleObjectsReturned):
                    pass

            elif use in ("preservation", "text/ocr", "derivative"):
                # Derived files (by AM or external) should be in the original file's group
                d = Derivation.objects.get(derived_file_id=f.uuid)
                GROUPID = "Group-" + d.source_file_id

            elif use == "service":
                # Service files are in the original file's group
                fileFileIDPath = itemdirectoryPath.replace(baseDirectoryPath + "objects/service/", baseDirectoryName + "objects/")
                objectNameExtensionIndex = fileFileIDPath.rfind(".")
                fileFileIDPath = fileFileIDPath[:objectNameExtensionIndex + 1]

                kwargs = {
                    "removedtime__isnull": True,
                    fileGroupType: fileGroupIdentifier,
                    "filegrpuse": "original",
                    "currentlocation__startswith": fileFileIDPath
                }
                original_file = File.objects.get(**kwargs)
                GROUPID = "Group-" + original_file.uuid

            elif use == "TRIM container metadata":
                GROUPID = "Group-%s" % (f.uuid)
                use = "metadata"

            # Special DSPACEMETS processing
            if f.transfer and f.transfer.type == "Dspace" and use == "DSPACEMETS":
                use = "submissionDocumentation"
                admidApplyTo = None
                if GROUPID == "":  # is an AIP identifier
                    GROUPID = f.uuid
                    admidApplyTo = structMapDiv.getparent()

                label = "mets.xml-%s" % (GROUPID)
                dspace_dmdsecs = createDSpaceDMDSec(label, itemdirectoryPath, directoryPathSTR)
                if dspace_dmdsecs:
                    dmdSecs.extend(dspace_dmdsecs.values())
                    ids = ' '.join(dspace_dmdsecs.keys())
                    if admidApplyTo is not None:
                        admidApplyTo.set("DMDID", ids)
                    else:
                        dspaceMetsDMDID = ids

            # If it's a .tab file, check if there's a Dataverse METS with additional metadata
            if f.originallocation.endswith('.tab'):
                dv_metadata = create_dataverse_tabfile_dmdsec(baseDirectoryPath, os.path.basename(f.originallocation))
                dmdSecs.extend(dv_metadata)
                ids = ' '.join([ds.get('ID') for ds in dv_metadata])
                fileDiv.attrib['DMDID'] = fileDiv.attrib.get('DMDID', '') + ' ' + ids

            if GROUPID == "":
                sharedVariablesAcrossModules.globalErrorCount += 1
                print("No groupID for file: \"", directoryPathSTR, "\"", file=sys.stderr)

            if use not in globalFileGrps:
                print('Invalid use: "%s"' % (use), file=sys.stderr)
                sharedVariablesAcrossModules.globalErrorCount += 1
            else:
                file_elem = etree.SubElement(globalFileGrps[use], ns.metsBNS + "file", ID=fileId, GROUPID=GROUPID)
                if use == "original":
                    filesInThisDirectory.append(file_elem)
                #<Flocat xlink:href="objects/file1-UUID" locType="other" otherLocType="system"/>
                newChild(file_elem, ns.metsBNS + "FLocat", sets=[(ns.xlinkBNS + "href", directoryPathSTR), ("LOCTYPE", "OTHER"), ("OTHERLOCTYPE", "SYSTEM")])
                if includeAmdSec:
                    AMD, ADMID = getAMDSec(f.uuid, directoryPathSTR, use, fileGroupType, fileGroupIdentifier, f.transfer_id, itemdirectoryPath, typeOfTransfer, baseDirectoryPath)
                    amdSecs.append(AMD)
                    file_elem.set("ADMID", ADMID)

    if dspaceMetsDMDID is not None:
        for file_elem in filesInThisDirectory:
            file_elem.set("DMDID", dspaceMetsDMDID)

    return structMapDiv

def build_arranged_structmap(original_structmap, sip_uuid):
    """
    Given a structMap, builds a new copy of the structMap with file and directory labels assigned according to their intellectual arrangement.
    Logical arrangement is determined using the levels of description which were assigned to them during SIP arrange.

    :param etree.Element original_structmap: the structMap on which the arranged structMap should be based.
    :param str sip_uuid: the SIP's UUID
    """
    tag_dict = dict(SIPArrange.objects.filter(sip_id=sip_uuid).values_list('arrange_path', 'level_of_description'))
    if not tag_dict:
        return

    structmap = copy.deepcopy(original_structmap)
    structmap.attrib['TYPE'] = 'logical'
    structmap.attrib['LABEL'] = 'Hierarchical'
    structmap.attrib['ID'] = "structMap_{}".format(uuid4())
    root_div = structmap.find('./mets:div', namespaces=ns.NSMAP)
    del root_div.attrib['TYPE']
    objects = root_div.find('./mets:div[@LABEL="objects"]', namespaces=ns.NSMAP)

    # The contents of submissionDocumentation and metadata do
    # not have intellectual arrangement, so don't need to be
    # represented in this structMap.
    for label in ('submissionDocumentation', 'metadata'):
        div = objects.find('.mets:div[@LABEL="{}"]'.format(label), namespaces=ns.NSMAP)
        if div is not None:
            objects.remove(div)

    # Handle objects level of description separately, since tag paths are relative to objects
    tag = tag_dict.get('.')
    if tag:
        print('Adding TYPE=%s for logical structMap element objects' % tag)
        objects.attrib['TYPE'] = tag
    else:
        del objects.attrib['TYPE']

    for element in objects.iterdescendants():
        if element.tag != ns.metsBNS + "div":
            continue

        # Build the full path relative to objects dir
        path = [element.attrib['LABEL']]
        parent = element.getparent()
        while parent != objects:
            path.insert(0, parent.attrib['LABEL'])
            parent = parent.getparent()
        relative_location = os.path.join(*path)

        # Certain items won't have a level of description;
        # they should be retained in the tree, but have
        # no TYPE attribute.
        tag = tag_dict.get(relative_location)
        if tag:
            print('Adding TYPE=%s for logical structMap element %s' % (tag, relative_location))
            element.attrib['TYPE'] = tag
        else:
            del element.attrib['TYPE']

    return structmap

def find_source_metadata(path):
    """
    Returns lists of all metadata to be referenced in the final document.
    This includes transfer metadata (embedded), and any XML metadata contained
    in the `metadata/sourceMD` directory from the original transfer (mdRef).

    The first returned list is the set of transfer metadata; the second is
    all other metadata to reference.
    """
    transfer = []
    source = []
    for dirpath, subdirs, filenames in os.walk(path):
        if 'transfer_metadata.xml' in filenames:
            transfer.append(os.path.join(dirpath, 'transfer_metadata.xml'))

        if 'sourceMD' in subdirs:
            pattern = os.path.join(dirpath, 'sourceMD', '*.xml')
            source.extend(glob(pattern))

    return transfer, source

def find_bag_metadata(bag_logs_path):
    try:
        return Bag(bag_logs_path).info
    except BagError:
        print("Unable to locate or parse bag metadata at: {}".format(bag_logs_path), file=sys.stderr)
        return {}

def create_object_metadata(struct_map, baseDirectoryPath):
    transfer_metadata_path = os.path.join(baseDirectoryPath, "objects/metadata/transfers")
    transfer, source = find_source_metadata(transfer_metadata_path)

    paths = glob(os.path.join(baseDirectoryPath, "logs", "transfers", "**", "logs", "BagIt"))
    bag_info = [find_bag_metadata(path) for path in paths]

    if not transfer and not source and not bag_info:
        return

    global globalAmdSecCounter

    globalAmdSecCounter += 1
    label = "amdSec_{}".format(globalAmdSecCounter)
    struct_map.set("ADMID", label)

    source_md_counter = 1

    el = etree.Element(ns.metsBNS + 'amdSec', {'ID': label})

    for filename in transfer:
        sourcemd = etree.SubElement(el, ns.metsBNS + 'sourceMD', {'ID': 'sourceMD_{}'.format(source_md_counter)})
        mdwrap = etree.SubElement(sourcemd, ns.metsBNS + 'mdWrap', {'MDTYPE': 'OTHER'})
        xmldata = etree.SubElement(mdwrap, ns.metsBNS + 'xmlData')
        source_md_counter += 1
        parser = etree.XMLParser(remove_blank_text=True)
        md = etree.parse(filename, parser)
        xmldata.append(md.getroot())

    for filename in source:
        sourcemd = etree.SubElement(el, ns.metsBNS + 'sourceMD', {'ID': 'sourceMD_{}'.format(source_md_counter)})
        source_md_counter += 1
        attributes = {
            ns.xlinkBNS + 'href': os.path.relpath(filename, baseDirectoryPath),
            'MDTYPE': 'OTHER',
            'LOCTYPE': 'OTHER',
            'OTHERLOCTYPE': 'SYSTEM'
        }
        etree.SubElement(sourcemd, ns.metsBNS + 'mdRef', attributes)

    for bagdata in bag_info:
        # If there are no tags, skip creating an element
        if not bagdata:
            continue

        sourcemd = etree.SubElement(el, ns.metsBNS + 'sourceMD', {'ID': 'sourceMD_{}'.format(source_md_counter)})
        source_md_counter += 1
        mdwrap = etree.SubElement(sourcemd, ns.metsBNS + 'mdWrap', {'MDTYPE': 'OTHER', 'OTHERMDTYPE': 'BagIt'})
        xmldata = etree.SubElement(mdwrap, ns.metsBNS + 'xmlData')
        bag_metadata = etree.SubElement(xmldata, "transfer_metadata")
        for key, value in bagdata.items():
            try:
                bag_tag = etree.SubElement(bag_metadata, key)
            except ValueError:
                print("Skipping bag key {}; not a valid XML tag name".format(key), file=sys.stderr)
                continue
            bag_tag.text = value

    return el


def write_mets(tree, filename):
    """
    Write tree to filename, and a validate METS form.

    :param ElementTree tree: METS ElementTree
    :param str filename: Filename to write the METS to
    """
    tree.write(filename, pretty_print=True, xml_declaration=True)

    import cgi
    validate_filename = filename + ".validatorTester.html"
    fileContents = """<html>
<body>
  <form method="post" action="http://pim.fcla.edu/validate/results">
    <label for="document">Enter XML Document:</label>
    <br/>
    <textarea id="directinput" rows="12" cols="76" name="document">%s</textarea>
    <br/>
    <br/>
    <input type="submit" value="Validate" />
    <br/>
  </form>
</body>
</html>""" % (cgi.escape(etree.tostring(tree, pretty_print=True, xml_declaration=True)))
    with open(validate_filename, 'w') as f:
        f.write(fileContents)

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.createMETS2")

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--sipType", action="store", dest="sip_type", default="SIP")
    parser.add_option("-s",  "--baseDirectoryPath", action="store", dest="baseDirectoryPath", default="")
    parser.add_option("-b",  "--baseDirectoryPathString", action="store", dest="baseDirectoryPathString", default="SIPDirectory") #transferDirectory/
    parser.add_option("-f",  "--fileGroupIdentifier", action="store", dest="fileGroupIdentifier", default="") #transferUUID/sipUUID
    parser.add_option("-t",  "--fileGroupType", action="store", dest="fileGroupType", default="sipUUID") #
    parser.add_option("-x",  "--xmlFile", action="store", dest="xmlFile", default="")
    parser.add_option("-a",  "--amdSec", action="store_true", dest="amdSec", default=False)
    (opts, args) = parser.parse_args()

    SIP_TYPE = opts.sip_type
    baseDirectoryPath = opts.baseDirectoryPath
    XMLFile = opts.xmlFile
    baseDirectoryPathString = "%%%s%%" % (opts.baseDirectoryPathString)
    fileGroupIdentifier = opts.fileGroupIdentifier
    fileGroupType = opts.fileGroupType
    includeAmdSec = opts.amdSec

    # If reingesting, do not create a new METS, just modify existing one
    if 'REIN' in SIP_TYPE:
        print('Updating METS during reingest')
        # fileGroupIdentifier is SIPUUID, baseDirectoryPath is SIP dir,
        tree = archivematicaCreateMETSReingest.update_mets(
            baseDirectoryPath,
            fileGroupIdentifier,
        )
        write_mets(tree, XMLFile)
        sys.exit(0)
    # End reingest

    CSV_METADATA = parseMetadata(baseDirectoryPath)

    baseDirectoryPath = os.path.join(baseDirectoryPath, '')
    objectsDirectoryPath = os.path.join(baseDirectoryPath, 'objects')

    # Delete empty directories, see #8427
    for root, dirs, files in os.walk(baseDirectoryPath, topdown=False):
        try:
            os.rmdir(root)
            print("Deleted empty directory", root)
        except OSError:
            pass

    structMap = etree.Element(ns.metsBNS + "structMap", TYPE='physical', ID='structMap_1', LABEL="Archivematica default")
    structMapDiv = etree.SubElement(structMap, ns.metsBNS + 'div', TYPE="Directory", LABEL=os.path.basename(baseDirectoryPath.rstrip('/')))
    structMapDivObjects = createFileSec(objectsDirectoryPath, structMapDiv, baseDirectoryPath, baseDirectoryPathString, fileGroupIdentifier, fileGroupType, includeAmdSec)

    el = create_object_metadata(structMapDivObjects, baseDirectoryPath)
    if el:
        amdSecs.append(el)

    # In an AIC, the metadata dir is not inside the objects dir
    metadataDirectoryPath = os.path.join(baseDirectoryPath, 'metadata')
    createFileSec(metadataDirectoryPath, structMapDiv, baseDirectoryPath, baseDirectoryPathString, fileGroupIdentifier, fileGroupType, includeAmdSec)

    fileSec = etree.Element(ns.metsBNS + "fileSec")
    for group in globalFileGrpsUses: #globalFileGrps.itervalues():
        grp = globalFileGrps[group]
        if len(grp) > 0:
            fileSec.append(grp)

    rootNSMap = {
        'mets': ns.metsNS,
        'xsi': ns.xsiNS,
        'xlink': ns.xlinkNS,
    }
    root = etree.Element(ns.metsBNS + "mets",
        nsmap = rootNSMap,
        attrib = { "{" + ns.xsiNS + "}schemaLocation" : "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd" },
    )
    etree.SubElement(root, ns.metsBNS + "metsHdr").set("CREATEDATE", timezone.now().strftime("%Y-%m-%dT%H:%M:%S"))

    dc = createDublincoreDMDSecFromDBData(SIPMetadataAppliesToType, fileGroupIdentifier, baseDirectoryPath)
    if dc != None:
        (dmdSec, ID) = dc
        if structMapDivObjects is not None:
            structMapDivObjects.set("DMDID", ID)
        else:
            # AICs have no objects directory but do have DC metadata
            # Attach the DC metadata to the top level SIP div
            # See #9822 for details
            structMapDiv.set('DMDID', ID)
        root.append(dmdSec)
    # Check for external (Dataverse) SIP-level dmdSecs
    dv = create_dataverse_sip_dmdsec(baseDirectoryPath)
    for dmdSec in dv:
        dmdid = dmdSec.attrib['ID']
        dmdids = structMapDivObjects.get("DMDID", '') + ' ' + dmdid
        structMapDivObjects.set("DMDID", dmdids)
        root.append(dmdSec)

    for dmdSec in dmdSecs:
        root.append(dmdSec)

    for amdSec in amdSecs:
        root.append(amdSec)

    root.append(fileSec)
    root.append(structMap)
    for structMapIncl in getIncludedStructMap(baseDirectoryPath):
        root.append(structMapIncl)

    arranged_structmap = build_arranged_structmap(structMap, fileGroupIdentifier)
    if arranged_structmap is not None:
        root.append(arranged_structmap)

    printSectionCounters = True
    if printSectionCounters:
        print("DmdSecs:", globalDmdSecCounter)
        print("AmdSecs:", globalAmdSecCounter)
        print("TechMDs:", globalTechMDCounter)
        print("RightsMDs:", globalRightsMDCounter)
        print("DigiprovMDs:", globalDigiprovMDCounter)

    tree = etree.ElementTree(root)
    write_mets(tree, XMLFile)

    sys.exit(sharedVariablesAcrossModules.globalErrorCount)
