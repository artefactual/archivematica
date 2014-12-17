#!/usr/bin/python -OO
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

from glob import glob
import lxml.etree as etree
import MySQLdb
import os
import re
import sys
import traceback

import archivematicaXMLNamesSpace as ns
from archivematicaCreateMETSMetadataCSV import parseMetadata
from archivematicaCreateMETSRights import archivematicaGetRights
from archivematicaCreateMETSRightsDspaceMDRef import archivematicaCreateMETSRightsDspaceMDRef
from archivematicaCreateMETSTrim import getTrimDmdSec
from archivematicaCreateMETSTrim import getTrimFileDmdSec
from archivematicaCreateMETSTrim import getTrimAmdSec
from archivematicaCreateMETSTrim import getTrimFileAmdSec
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from archivematicaFunctions import escape
from archivematicaFunctions import strToUnicode
from archivematicaFunctions import normalizeNonDcElementName
from sharedVariablesAcrossModules import sharedVariablesAcrossModules
sharedVariablesAcrossModules.globalErrorCount = 0

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-s",  "--baseDirectoryPath", action="store", dest="baseDirectoryPath", default="")
parser.add_option("-b",  "--baseDirectoryPathString", action="store", dest="baseDirectoryPathString", default="SIPDirectory") #transferDirectory/
parser.add_option("-f",  "--fileGroupIdentifier", action="store", dest="fileGroupIdentifier", default="") #transferUUID/sipUUID
parser.add_option("-t",  "--fileGroupType", action="store", dest="fileGroupType", default="sipUUID") #
parser.add_option("-x",  "--xmlFile", action="store", dest="xmlFile", default="")
parser.add_option("-a",  "--amdSec", action="store_true", dest="amdSec", default=False)
(opts, args) = parser.parse_args()


baseDirectoryPath = opts.baseDirectoryPath
XMLFile = opts.xmlFile
includeAmdSec = opts.amdSec
baseDirectoryPathString = "%%%s%%" % (opts.baseDirectoryPathString)
fileGroupIdentifier = opts.fileGroupIdentifier
fileGroupType = opts.fileGroupType
includeAmdSec = opts.amdSec

#Global Variables

globalFileGrps = {}
globalFileGrpsUses = ["original", "submissionDocumentation", "preservation", "service", "access", "license", "text/ocr", "metadata"]
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

def createAgent(agentIdentifierType, agentIdentifierValue, agentName, agentType):
    agent = etree.Element(ns.premisBNS + "agent", nsmap={'premis': ns.premisNS})
    agent.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    agent.set("version", "2.2")

    agentIdentifier = etree.SubElement(agent, ns.premisBNS + "agentIdentifier")
    etree.SubElement(agentIdentifier, ns.premisBNS + "agentIdentifierType").text = agentIdentifierType
    etree.SubElement(agentIdentifier, ns.premisBNS + "agentIdentifierValue").text = agentIdentifierValue
    etree.SubElement(agent, ns.premisBNS + "agentName").text = agentName
    etree.SubElement(agent, ns.premisBNS + "agentType").text = agentType
    return agent


SIPMetadataAppliesToType = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'
TransferMetadataAppliesToType = '45696327-44c5-4e78-849b-e027a189bf4d'
FileMetadataAppliesToType = '7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17'
def getDublinCore(unit, id):
    field_list = ["title", "creator", "subject", "description", "publisher", "contributor", "date", "type", "format", "identifier", "source", "relation", "language", "coverage", "rights", "isPartOf"]
    sql = """SELECT {fields}
    FROM Dublincore WHERE metadataAppliesToType = '{type}' AND metadataAppliesToidentifier = '{id}';""".format(
            fields=', '.join(field_list),
            type=unit,
            id=id)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    ret = None
    if row is not None:
        ret = etree.Element(ns.dctermsBNS + "dublincore", nsmap={"dc":ns.dctermsNS})
        ret.set(ns.xsiBNS+"schemaLocation", ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
    while row is not None:
        #title, creator, subject, description, publisher, contributor, date, type, format, identifier, source, relation, language, coverage, rights = row
        for i, term in enumerate(field_list):
            txt = row[i] or ""
            if txt:
                newChild(ret, ns.dctermsBNS + term, text=txt)
        row = c.fetchone()
    sqlLock.release()
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
    global globalDmdSecCounter
    global dmdSecs
    dc = None
    other = None
    ret = []

    # Archivematica does not support refined Dublin Core, e.g.
    # multitiered terms in the format dc.description.abstract
    # If these terms are encountered, an element with only the
    # last portion of the name will be added.
    # e.g., dc.description.abstract is mapped to <dcterms:abstract>
    refinement_regex = re.compile('\w+\.(.+)')

    for key, value in metadata.iteritems():
        if key.startswith("dc.") or key.startswith("dcterms."):
            #print "dc item: ", key, value
            if dc is None:
                globalDmdSecCounter += 1
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                dmdSec = etree.Element(ns.metsBNS + "dmdSec", ID=ID)
                dmdSecs.append(dmdSec)
                ret.append(dmdSec)
                mdWrap = etree.SubElement(dmdSec, ns.metsBNS + "mdWrap")
                mdWrap.set("MDTYPE", "DC")
                xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
                dc = etree.Element(ns.dctermsBNS + "dublincore", nsmap={"dc": ns.dctermsNS})
                dc.set(ns.xsiBNS+"schemaLocation", ns.dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
                xmlData.append(dc)
            if key.startswith("dc."):
                key2 = key.replace("dc.", "", 1)
            elif key.startswith("dcterms."):
                key2 = key.replace("dcterms.", "", 1)
            value = value.decode('utf-8')
            match = re.match(refinement_regex, key2)
            if match:
                key2, = match.groups()

            el = etree.SubElement(dc, ns.dctermsBNS + key2)
            el.text = value
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
            etree.SubElement(other, normalizeNonDcElementName(key)).text = value
    return ret


def createDublincoreDMDSecFromDBData(type, id):
    dc = getDublinCore(type, id)
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
                except Exception as inst:
                    print >>sys.stderr, "error parsing file:", dcXMLFile
                    print >>sys.stderr, type(inst)     # the exception instance
                    print >>sys.stderr, inst.args
                    traceback.print_exc(file=sys.stdout)
                    sharedVariablesAcrossModules.globalErrorCount += 1
                    return None
            else:
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

def createMDRefDMDSec(LABEL, itemdirectoryPath, directoryPathSTR):
    global globalDmdSecCounter
    globalDmdSecCounter += 1
    dmdSec = etree.Element(ns.metsBNS + "dmdSec")
    ID = "dmdSec_" + globalDmdSecCounter.__str__()
    dmdSec.set("ID", ID)
    XPTR = "xpointer(id("
    tree = etree.parse(itemdirectoryPath)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}dmdSec"):
        XPTR = "%s %s" % (XPTR, item.get("ID"))
    XPTR = XPTR.replace(" ", "'", 1) + "'))"
    newChild(dmdSec, ns.metsBNS + "mdRef", text=None, sets=[("LABEL", LABEL), (ns.xlinkBNS +"href", directoryPathSTR), ("MDTYPE", "OTHER"), ("LOCTYPE","OTHER"), ("OTHERLOCTYPE", "SYSTEM"), ("XPTR", XPTR)])
    return (dmdSec, ID)


def createTechMD(fileUUID):
    ret = etree.Element(ns.metsBNS + "techMD")
    techMD = ret #newChild(amdSec, "digiprovMD")
    #digiprovMD.set("ID", "digiprov-"+ os.path.basename(filename) + "-" + fileUUID)
    global globalTechMDCounter
    globalTechMDCounter += 1
    techMD.set("ID", "techMD_"+ globalTechMDCounter.__str__())

    mdWrap = etree.SubElement(techMD, ns.metsBNS + "mdWrap")
    mdWrap.set("MDTYPE", "PREMIS:OBJECT")
    xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
    #premis = etree.SubElement( xmlData, "premis", nsmap={None: ns.premisNS}, \
    #    attrib = { "{" + ns.xsiNS + "}schemaLocation" : "info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/premis.xsd" })
    #premis.set("version", "2.0")

    #premis = etree.SubElement( xmlData, "premis", attrib = {ns.xsiBNS+"type": "premis:file"})

    sql = "SELECT fileSize, checksum FROM Files WHERE fileUUID = '%s';" % (fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        fileSize = row[0].__str__()
        checksum = row[1].__str__()
        row = c.fetchone()
    sqlLock.release()

    #OBJECT
    object = etree.SubElement(xmlData, ns.premisBNS + "object", nsmap={'premis': ns.premisNS})
    object.set(ns.xsiBNS+"type", "premis:file")
    object.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    object.set("version", "2.2")

    objectIdentifier = etree.SubElement(object, ns.premisBNS + "objectIdentifier")
    etree.SubElement(objectIdentifier, ns.premisBNS + "objectIdentifierType").text = "UUID"
    etree.SubElement(objectIdentifier, ns.premisBNS + "objectIdentifierValue").text = fileUUID

    #etree.SubElement(object, "objectCategory").text = "file"

    objectCharacteristics = etree.SubElement(object, ns.premisBNS + "objectCharacteristics")
    etree.SubElement(objectCharacteristics, ns.premisBNS + "compositionLevel").text = "0"

    fixity = etree.SubElement(objectCharacteristics, ns.premisBNS + "fixity")
    etree.SubElement(fixity, ns.premisBNS + "messageDigestAlgorithm").text = "sha256"
    etree.SubElement(fixity, ns.premisBNS + "messageDigest").text = checksum

    etree.SubElement(objectCharacteristics, ns.premisBNS + "size").text = fileSize

    sql = "SELECT formatName, formatVersion, formatRegistryName, formatRegistryKey FROM FilesIDs WHERE fileUUID = '%s';" % (fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    if not row:
        format = etree.SubElement(objectCharacteristics, ns.premisBNS + "format")
        formatDesignation = etree.SubElement(format, ns.premisBNS + "formatDesignation")
        etree.SubElement(formatDesignation, ns.premisBNS + "formatName").text = "Unknown"
    while row != None:
        #print row
        format = etree.SubElement(objectCharacteristics, ns.premisBNS + "format")
        #fileUUID = row[0]

        formatDesignation = etree.SubElement(format, ns.premisBNS + "formatDesignation")
        etree.SubElement(formatDesignation, ns.premisBNS + "formatName").text = row[0]
        etree.SubElement(formatDesignation, ns.premisBNS + "formatVersion").text = row[1]

        formatRegistry = etree.SubElement(format, ns.premisBNS + "formatRegistry")
        etree.SubElement(formatRegistry, ns.premisBNS + "formatRegistryName").text = row[2]
        etree.SubElement(formatRegistry, ns.premisBNS + "formatRegistryKey").text = row[3]
        row = c.fetchone()
    sqlLock.release()

    objectCharacteristicsExtension = etree.SubElement(objectCharacteristics, ns.premisBNS + "objectCharacteristicsExtension")

    sql = "SELECT FPCommandOutput.content FROM FPCommandOutput \
           INNER JOIN fpr_fprule ON FPCommandOutput.ruleUUID = fpr_fprule.uuid \
           WHERE fileUUID = '{file}' AND (purpose = 'characterization' OR purpose = 'default_characterization');".format(file=fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    parser = etree.XMLParser(remove_blank_text=True)
    for document, in c:
        # This needs to be converted into an str because lxml doesn't accept
        # XML documents in unicode strings if the document contains an
        # encoding declaration.
        output = etree.XML(document.encode("utf-8"), parser)
        objectCharacteristicsExtension.append(output)
    sqlLock.release()

    sql = "SELECT Files.originalLocation FROM Files WHERE Files.fileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    if not row:
        print >>sys.stderr, "Error: no location found."
    while row != None:
        etree.SubElement(object, ns.premisBNS + "originalName").text = escape(row[0])
        row = c.fetchone()
    sqlLock.release()

    #Derivations
    sql = "SELECT sourceFileUUID, derivedFileUUID, relatedEventUUID FROM Derivations WHERE sourceFileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        relationship = etree.SubElement(object, ns.premisBNS + "relationship")
        etree.SubElement(relationship, ns.premisBNS + "relationshipType").text = "derivation"
        etree.SubElement(relationship, ns.premisBNS + "relationshipSubType").text = "is source of"

        relatedObjectIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierValue").text = row[1]

        relatedEventIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierValue").text = row[2]

        row = c.fetchone()
    sqlLock.release()

    sql = "SELECT sourceFileUUID, derivedFileUUID, relatedEventUUID FROM Derivations WHERE derivedFileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        relationship = etree.SubElement(object, ns.premisBNS + "relationship")
        etree.SubElement(relationship, ns.premisBNS + "relationshipType").text = "derivation"
        etree.SubElement(relationship, ns.premisBNS + "relationshipSubType").text = "has source"

        relatedObjectIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, ns.premisBNS + "relatedObjectIdentifierValue").text = row[0]

        relatedEventIdentification = etree.SubElement(relationship, ns.premisBNS + "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, ns.premisBNS + "relatedEventIdentifierValue").text = row[2]

        row = c.fetchone()
    sqlLock.release()
    return ret

def createDigiprovMD(fileUUID):
    ret = []
    #EVENTS

    sql = "SELECT pk, fileUUID, eventIdentifierUUID, eventType, eventDateTime, eventDetail, eventOutcome, eventOutcomeDetailNote, linkingAgentIdentifier FROM Events WHERE fileUUID = '" + fileUUID + "';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD")
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        #digiprovMD.set("ID", "digiprov-"+ os.path.basename(filename) + "-" + fileUUID)
        global globalDigiprovMDCounter
        globalDigiprovMDCounter += 1
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())

        mdWrap = etree.SubElement(digiprovMD, ns.metsBNS + "mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:EVENT")
        xmlData = etree.SubElement(mdWrap, ns.metsBNS + "xmlData")
        event = etree.SubElement(xmlData, ns.premisBNS + "event", nsmap={'premis': ns.premisNS})
        event.set(ns.xsiBNS+"schemaLocation", ns.premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
        event.set("version", "2.2")

        eventIdentifier = etree.SubElement(event, ns.premisBNS + "eventIdentifier")
        etree.SubElement(eventIdentifier, ns.premisBNS + "eventIdentifierType").text = "UUID"
        etree.SubElement(eventIdentifier, ns.premisBNS + "eventIdentifierValue").text = row[2]

        etree.SubElement(event, ns.premisBNS + "eventType").text = row[3]
        etree.SubElement(event, ns.premisBNS + "eventDateTime").text = row[4].__str__().replace(" ", "T")
        etree.SubElement(event, ns.premisBNS + "eventDetail").text = escape(row[5])

        eventOutcomeInformation  = etree.SubElement(event, ns.premisBNS + "eventOutcomeInformation")
        etree.SubElement(eventOutcomeInformation, ns.premisBNS + "eventOutcome").text = row[6]
        eventOutcomeDetail = etree.SubElement(eventOutcomeInformation, ns.premisBNS + "eventOutcomeDetail")
        etree.SubElement(eventOutcomeDetail, ns.premisBNS + "eventOutcomeDetailNote").text = escape(row[7])
        
        if row[8]:
            linkingAgentIdentifier = etree.SubElement(event, ns.premisBNS + "linkingAgentIdentifier")
            etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierType").text = "Archivematica user pk"
            etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierValue").text = row[8].__str__()
        
        #linkingAgentIdentifier
        sql = """SELECT agentIdentifierType, agentIdentifierValue, agentName, agentType FROM Agents;"""
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            linkingAgentIdentifier = etree.SubElement(event, ns.premisBNS + "linkingAgentIdentifier")
            etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierType").text = row[0]
            etree.SubElement(linkingAgentIdentifier, ns.premisBNS + "linkingAgentIdentifierValue").text = row[1]
            row = c.fetchone()
        sqlLock.release()
    return ret

def createDigiprovMDAgents():
    ret = []
    global globalDigiprovMDCounter
    #AGENTS
    sql = """SELECT agentIdentifierType, agentIdentifierValue, agentName, agentType FROM Agents;"""
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        globalDigiprovMDCounter += 1
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD")
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        mdWrap = newChild(digiprovMD, ns.metsBNS + "mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:AGENT")
        xmlData = newChild(mdWrap, ns.metsBNS + "xmlData")
        #agents = etree.SubElement(xmlData, "agents")
        xmlData.append(createAgent(row[0], row[1], row[2], row[3]))
        row = c.fetchone()
    sqlLock.release()
    
    sql = """SELECT auth_user.id, auth_user.username, auth_user.first_name, auth_user.last_name FROM SIPs JOIN Files ON SIPs.sipUUID = Files.sipUUID JOIN Events ON Files.fileUUID = Events.fileUUID JOIN auth_user ON Events.linkingAgentIdentifier = auth_user.id WHERE SIPs.sipUUID = '%s' GROUP BY auth_user.id;""" % (fileGroupIdentifier)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        globalDigiprovMDCounter += 1
        digiprovMD = etree.Element(ns.metsBNS + "digiprovMD")
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        mdWrap = newChild(digiprovMD, ns.metsBNS + "mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:AGENT")
        xmlData = newChild(mdWrap, ns.metsBNS + "xmlData")
        #agents = etree.SubElement(xmlData, "agents")
        
        id, username, first_name, last_name = row
        id = id.__str__()
        if not username:
            username = ""
        if not first_name:
            first_name = ""
        if not last_name:
            last_name = ""
        agentIdentifierType = "Archivematica user pk"
        agentIdentifierValue = id
        agentName = 'username="%s", first_name="%s", last_name="%s"' % (username, first_name, last_name)       
        agentType = "Archivematica user"
        xmlData.append(createAgent(agentIdentifierType, agentIdentifierValue, agentName, agentType))
        row = c.fetchone()
    sqlLock.release()
    
    return ret



def getAMDSec(fileUUID, filePath, use, type, id, transferUUID, itemdirectoryPath, typeOfTransfer):
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
        metadataAppliesToList = [(fileUUID, FileMetadataAppliesToType), (fileGroupIdentifier, SIPMetadataAppliesToType), (transferUUID.__str__(), TransferMetadataAppliesToType)]
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
            digiprovMD = getTrimFileAmdSec(baseDirectoryPath, fileGroupIdentifier, fileUUID)
            globalDigiprovMDCounter += 1
            digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
            AMD.append(digiprovMD)

    for a in createDigiprovMD(fileUUID):
        AMD.append(a)

    for a in createDigiprovMDAgents():
        AMD.append(a)
    return ret

def getIncludedStructMap():
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
                    print >>sys.stderr,"error: no fileUUID for ", fileName
                    sharedVariablesAcrossModules.globalErrorCount += 1
    for fileName, fileID in  fileNameToFileID.iteritems():
        #locate file based on key
        continue
        print fileName 
    if trimStructMap != None:
        ret.append(trimStructMap)
    return ret

#DMDID="dmdSec_01" for an object goes in here
#<file ID="file1-UUID" GROUPID="G1" DMDID="dmdSec_02" ADMID="amdSec_01">
def createFileSec(directoryPath, parentDiv):
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
        directoryContents = os.listdir(directoryPath)
    except os.error:
        # Directory doesn't exist
        print >> sys.stderr, directoryPath, "doesn't exist"
        return

    structMapDiv = etree.SubElement(parentDiv, ns.metsBNS + 'div', TYPE='Directory', LABEL=os.path.basename(directoryPath))

    DMDIDS = createDMDIDsFromCSVMetadata(directoryPath.replace(baseDirectoryPath, "", 1))
    if DMDIDS:
        structMapDiv.set("DMDID", DMDIDS)

    for item in directoryContents:
        itemdirectoryPath = os.path.join(directoryPath, item)
        if os.path.isdir(itemdirectoryPath):
            createFileSec(itemdirectoryPath, structMapDiv)
        elif os.path.isfile(itemdirectoryPath):
            myuuid=""
            DMDIDS=""
            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, baseDirectoryPathString, 1)

            sql = """SELECT fileUUID, fileGrpUse, fileGrpUUID, Files.transferUUID, label, originalLocation, Transfers.type
                    FROM Files
                    LEFT OUTER JOIN Transfers ON Files.transferUUID = Transfers.transferUUID
                    WHERE removedTime = 0 AND %s = '%s' AND Files.currentLocation = '%s';""" % (fileGroupType, fileGroupIdentifier, MySQLdb.escape_string(directoryPathSTR))
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            if row == None:
                print >>sys.stderr, "No uuid for file: \"", directoryPathSTR, "\""
                sharedVariablesAcrossModules.globalErrorCount += 1
                sqlLock.release()
                continue
            while row != None:
                myuuid = row[0]
                use = row[1]
                fileGrpUUID = row[2]
                transferUUID = row[3]
                label = row[4]
                originalLocation = row[5]
                typeOfTransfer = row[6]
                row = c.fetchone()
            sqlLock.release()
            
            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, "", 1)

            if typeOfTransfer == "TRIM" and trimStructMap is None:
                trimStructMap = etree.Element(ns.metsBNS + "structMap", attrib={"TYPE":"logical", "ID":"structMap_2", "LABEL":"Hierarchical arrangement"})
                trimStructMapObjects = etree.SubElement(trimStructMap, ns.metsBNS + "div", attrib={"TYPE":"File", "LABEL":"objects"})

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
                digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())

                trimAmdSec.append(digiprovMD)

                trimStructMapObjects.set("ADMID", ID)

            fileId="file-%s" % (myuuid, )

            #<fptr FILEID="file-<UUID>" LABEL="filename.ext">
            label = item if label is None else label
            fileDiv = etree.SubElement(structMapDiv, ns.metsBNS + "div", LABEL=label, TYPE='Item')
            etree.SubElement(fileDiv, ns.metsBNS + 'fptr', FILEID=fileId)
            fileNameToFileID[item] = fileId

            GROUPID = ""
            if fileGrpUUID:
                GROUPID = "Group-%s" % (fileGrpUUID)
                if use == "TRIM file metadata":
                    use = "metadata"

            elif use in ("original", "submissionDocumentation", "metadata", "maildirFile"):
                GROUPID = "Group-%s" % (myuuid)
                if use == "maildirFile":
                    use = "original"
                if use == "original":
                    DMDIDS = createDMDIDsFromCSVMetadata(originalLocation.replace('%transferDirectory%', "", 1))
                    if DMDIDS:
                        fileDiv.set("DMDID", DMDIDS)
                    if typeOfTransfer == "TRIM":
                        trimFileDiv = etree.SubElement(trimStructMapObjects, ns.metsBNS + "div", attrib={"TYPE":"Item"})
                        
                        trimFileDmdSec = getTrimFileDmdSec(baseDirectoryPath, fileGroupIdentifier, myuuid)
                        globalDmdSecCounter += 1
                        dmdSecs.append(trimFileDmdSec)
                        ID = "dmdSec_" + globalDmdSecCounter.__str__()
                        trimFileDmdSec.set("ID", ID)

                        trimFileDiv.set("DMDID", ID)

                        etree.SubElement(trimFileDiv, ns.metsBNS + "fptr", FILEID=fileId)

            # Dspace transfers are treated specially, but some of these fileGrpUses
            # may be encountered in other types
            elif typeOfTransfer == "Dspace" and (use in ("license", "text/ocr", "DSPACEMETS")):
                sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND %s = '%s' AND fileGrpUse = 'original' AND originalLocation LIKE '%s/%%'""" % (fileGroupType, fileGroupIdentifier, MySQLdb.escape_string(os.path.dirname(originalLocation)).replace("%", "\%"))
                c, sqlLock = databaseInterface.querySQL(sql)
                row = c.fetchone()
                while row != None:
                    GROUPID = "Group-%s" % (row[0])
                    row = c.fetchone()
                sqlLock.release()

            elif use == "preservation" or use == "text/ocr":
                sql = "SELECT * FROM Derivations WHERE derivedFileUUID = '" + myuuid + "';"
                c, sqlLock = databaseInterface.querySQL(sql)
                row = c.fetchone()
                while row != None:
                    GROUPID = "Group-%s" % (row[1])
                    row = c.fetchone()
                sqlLock.release()

            elif use == "service":
                fileFileIDPath = itemdirectoryPath.replace(baseDirectoryPath + "objects/service/", baseDirectoryPathString + "objects/")
                objectNameExtensionIndex = fileFileIDPath.rfind(".")
                fileFileIDPath = fileFileIDPath[:objectNameExtensionIndex + 1]
                sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND %s = '%s' AND fileGrpUse = 'original' AND currentLocation LIKE '%s%%'""" % (fileGroupType, fileGroupIdentifier, MySQLdb.escape_string(fileFileIDPath.replace("%", "\%")))
                c, sqlLock = databaseInterface.querySQL(sql)
                row = c.fetchone()
                while row != None:
                    GROUPID = "Group-%s" % (row[0])
                    row = c.fetchone()
                sqlLock.release()
            
            
            elif use == "TRIM container metadata":
                GROUPID = "Group-%s" % (myuuid)
                use = "metadata"
            

            if transferUUID:
                sql = "SELECT type FROM Transfers WHERE transferUUID = '%s';" % (transferUUID)
                rows = databaseInterface.queryAllSQL(sql)
                if rows[0][0] == "Dspace":
                    if use == "DSPACEMETS":
                        use = "submissionDocumentation"
                        admidApplyTo = None
                        if GROUPID=="": #is an AIP identifier
                            GROUPID = myuuid
                            admidApplyTo = structMapDiv.getparent()


                        LABEL = "mets.xml-%s" % (GROUPID)
                        dmdSec, ID = createMDRefDMDSec(LABEL, itemdirectoryPath, directoryPathSTR)
                        dmdSecs.append(dmdSec)
                        if admidApplyTo != None:
                            admidApplyTo.set("DMDID", ID)
                        else:
                            dspaceMetsDMDID = ID

            if GROUPID=="":
                sharedVariablesAcrossModules.globalErrorCount += 1
                print >>sys.stderr, "No groupID for file: \"", directoryPathSTR, "\""

            if use not in globalFileGrps:
                print >>sys.stderr, "Invalid use: \"%s\"" % (use)
                sharedVariablesAcrossModules.globalErrorCount += 1
            else:
                file_elem = etree.SubElement(globalFileGrps[use], ns.metsBNS + "file", ID=fileId, GROUPID=GROUPID)
                if use == "original":
                    filesInThisDirectory.append(file_elem)
                #<Flocat xlink:href="objects/file1-UUID" locType="other" otherLocType="system"/>
                newChild(file_elem, ns.metsBNS + "FLocat", sets=[(ns.xlinkBNS +"href",directoryPathSTR), ("LOCTYPE","OTHER"), ("OTHERLOCTYPE", "SYSTEM")])
                if includeAmdSec:
                    AMD, ADMID = getAMDSec(myuuid, directoryPathSTR, use, fileGroupType, fileGroupIdentifier, transferUUID, itemdirectoryPath, typeOfTransfer)
                    amdSecs.append(AMD)
                    file_elem.set("ADMID", ADMID)

    if dspaceMetsDMDID != None:
        for file_elem in filesInThisDirectory:
            file_elem.set("DMDID", dspaceMetsDMDID)
    
    return structMapDiv
        
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

def create_object_metadata(struct_map):
    transfer_metadata_path = os.path.join(baseDirectoryPath, "objects/metadata/transfers")
    transfer, source = find_source_metadata(transfer_metadata_path)
    if not transfer and not source:
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

    return el


if __name__ == '__main__':
    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)

    CSV_METADATA = parseMetadata(baseDirectoryPath)

    if not baseDirectoryPath.endswith('/'):
        baseDirectoryPath += '/'
    structMap = etree.Element(ns.metsBNS + "structMap", TYPE='physical', ID='structMap_1', LABEL="Archivematica default")
    structMapDiv = etree.SubElement(structMap, ns.metsBNS + 'div', TYPE="Directory", LABEL=os.path.basename(baseDirectoryPath.rstrip('/')))
    structMapDivObjects = createFileSec(os.path.join(baseDirectoryPath, "objects"), structMapDiv)

    el = create_object_metadata(structMapDivObjects)
    if el:
        amdSecs.append(el)

    createFileSec(os.path.join(baseDirectoryPath, "metadata"), structMapDiv)


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
    etree.SubElement(root, ns.metsBNS + "metsHdr").set("CREATEDATE", databaseInterface.getUTCDate().split(".")[0])



    dc = createDublincoreDMDSecFromDBData(SIPMetadataAppliesToType, fileGroupIdentifier)
    if dc != None:
        (dmdSec, ID) = dc
        structMapDivObjects.set("DMDID", ID)
        root.append(dmdSec)

    for dmdSec in dmdSecs:
        root.append(dmdSec)

    for amdSec in amdSecs:
        root.append(amdSec)

    root.append(fileSec)
    root.append(structMap)
    for structMapIncl in getIncludedStructMap():
        root.append(structMapIncl)
    if False: #debug
        print etree.tostring(root, pretty_print=True)

    #<div TYPE="directory" LABEL="AIP1-UUID">
    #<div TYPE="directory" LABEL="objects" DMDID="dmdSec_01">
    #Recursive function for creating structmap and fileSec
    tree = etree.ElementTree(root)
    #tree.write(XMLFile)
    tree.write(XMLFile, pretty_print=True, xml_declaration=True)

    printSectionCounters = True
    if printSectionCounters:
        print "DmdSecs:", globalDmdSecCounter
        print "AmdSecs:", globalAmdSecCounter
        print "TechMDs:", globalTechMDCounter
        print "RightsMDs:", globalRightsMDCounter
        print "DigiprovMDs:", globalDigiprovMDCounter
         
    writeTestXMLFile = True
    if writeTestXMLFile:
        import cgi
        fileName = XMLFile + ".validatorTester.html"
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
</html>""" % (cgi.escape(etree.tostring(root, pretty_print=True, xml_declaration=True)))
        f = open(fileName, 'w')
        f.write(fileContents)
        f.close

    exit(sharedVariablesAcrossModules.globalErrorCount)
