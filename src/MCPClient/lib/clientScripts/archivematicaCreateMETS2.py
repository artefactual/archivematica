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
from archivematicaXMLNamesSpace import *
import lxml.etree as etree
from xml.sax.saxutils import quoteattr
from glob import glob
import os
import sys
import MySQLdb
import PyICU
import traceback
from archivematicaCreateMETSMetadataCSV import parseMetadata
from archivematicaCreateMETSMetadataCSV import CSVMetadata
from archivematicaCreateMETSRights import archivematicaGetRights
from archivematicaCreateMETSRightsDspaceMDRef import archivematicaCreateMETSRightsDspaceMDRef
from archivematicaCreateMETSTrim import getTrimDmdSec
from archivematicaCreateMETSTrim import getTrimFileDmdSec
from archivematicaCreateMETSTrim import getTrimAmdSec
from archivematicaCreateMETSTrim import getTrimFileAmdSec
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import databaseInterface
from archivematicaFunctions import escape
from archivematicaFunctions import unicodeToStr
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
parser.add_option("-i",  "--PyICULocale", action="store", dest="PyICULocale", default='pl_PL.UTF-8')
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
    grp = etree.Element("fileGrp")
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
globalAmdSecCounter = 1
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

#move to common
def newChild(parent, tag, text=None, tailText=None, sets=[]):
    child = etree.Element(tag)
    parent.append(child)
    child.text = strToUnicode(text)
    if tailText:
        child.tail = strToUnicode(tailText)
    for set in sets:
        key, value = set
        child.set(key, value)
    return child

def createAgent(agentIdentifierType, agentIdentifierValue, agentName, agentType):
    ret = etree.Element("agent")
    agentIdentifier = etree.SubElement( ret, "agentIdentifier")
    etree.SubElement( agentIdentifier, "agentIdentifierType").text = agentIdentifierType
    etree.SubElement( agentIdentifier, "agentIdentifierValue").text = agentIdentifierValue
    etree.SubElement( ret, "agentName").text = agentName
    etree.SubElement( ret, "agentType").text = agentType
    return ret


SIPMetadataAppliesToType = '3e48343d-e2d2-4956-aaa3-b54d26eb9761'
TransferMetadataAppliesToType = '45696327-44c5-4e78-849b-e027a189bf4d'
FileMetadataAppliesToType = '7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17'
def getDublinCore(type_, id):
    sql = """SELECT     title, creator, subject, description, publisher, contributor, date, type, format, identifier, source, relation, language, coverage, rights
    FROM Dublincore WHERE metadataAppliesToType = '%s' AND metadataAppliesToidentifier = '%s';""" % \
    (type_.__str__(), id.__str__())
    
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    if row == None:
        sqlLock.release()
        return None
    ret = etree.Element( "dublincore", nsmap = {None:dctermsNS} )
    ret.set(xsiBNS+"schemaLocation", dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
    dctermsElements= ["isPartOf"]
    while row != None:
        key = ["title", "creator", "subject", "description", "publisher", "contributor", "date", "type", "format", "identifier", "source", "relation", "language", "coverage", "rights"]
        #title, creator, subject, description, publisher, contributor, date, type, format, identifier, source, relation, language, coverage, rights = row
        #key.index("title") == title
        i = 0
        for term in key:
            if row[i] != None:
                txt = row[i]
            else:
                txt = ""
            newChild(ret, term, text=txt)
            i+=1

        row = c.fetchone()
    sqlLock.release()
    return ret


def createDMDIDSFromCSVParsedMetadataFiles(filePath):
    simpleMetadataCSVkey, simpleMetadataCSV, compoundMetadataCSVkey, compoundMetadataCSV = CSVMetadata
    if filePath in simpleMetadataCSV:
        return createDMDIDSFromCSVParsedMetadataPart2(simpleMetadataCSVkey, simpleMetadataCSV[filePath])

def createDMDIDSFromCSVParsedMetadataDirectories(directory):
    simpleMetadataCSVkey, simpleMetadataCSV, compoundMetadataCSVkey, compoundMetadataCSV = CSVMetadata
    for key, values in compoundMetadataCSV.iteritems():
        if directory == key:
            return createDMDIDSFromCSVParsedMetadataPart2(compoundMetadataCSVkey, values)

                
def createDMDIDSFromCSVParsedMetadataPart2(keys, values):
    global globalDmdSecCounter
    global dmdSecs
    dc = None
    other = None
    ret = []
    for i in range(1, len(keys)):
        key = keys[i]
        value = values[i]
        if key.startswith("dc.") or key.startswith("dcterms."):
            #print "dc item: ", key, value
            if dc == None:
                globalDmdSecCounter += 1
                dmdSec = etree.Element("dmdSec")
                dmdSecs.append(dmdSec)
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                ret.append(ID)
                dmdSec.set("ID", ID)
                mdWrap = newChild(dmdSec, "mdWrap")
                mdWrap.set("MDTYPE", "DC")
                xmlData = newChild(mdWrap, "xmlData")
                dc = etree.Element( "dublincore", nsmap = {None: dctermsNS} )
                dc.set(xsiBNS+"schemaLocation", dctermsNS + " http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd")
                xmlData.append(dc)
            if key.startswith("dc."):
                key2 = key.replace("dc.", "", 1)
            elif  key.startswith("dcterms."):
                key2 = key.replace("dcterms.", "", 1)
            value = value.decode('utf-8')
            etree.SubElement(dc, key2).text = value
        else: #not a dublin core item
            #print "non dc: ", key, value
            if other == None:
                globalDmdSecCounter += 1
                dmdSec = etree.Element("dmdSec")
                dmdSecs.append(dmdSec)
                ID = "dmdSec_" + globalDmdSecCounter.__str__()
                ret.append(ID)
                dmdSec.set("ID", ID)
                mdWrap = newChild(dmdSec, "mdWrap")
                mdWrap.set("MDTYPE", "OTHER")
                mdWrap.set("OTHERMDTYPE", "CUSTOM")
                other = newChild(mdWrap, "xmlData")
            etree.SubElement(other, normalizeNonDcElementName(key)).text = value
    return  " ".join(ret)
            
    

def createDublincoreDMDSecFromDBData(type, id):
    dc = getDublinCore(type, id)
    if dc == None:
        transfers = os.path.join(baseDirectoryPath, "objects/metadata/transfers/")
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
    dmdSec = etree.Element("dmdSec")
    ID = "dmdSec_" + globalDmdSecCounter.__str__()
    dmdSec.set("ID", ID)
    mdWrap = newChild(dmdSec, "mdWrap")
    mdWrap.set("MDTYPE", "DC")
    xmlData = newChild(mdWrap, "xmlData")
    xmlData.append(dc)
    return (dmdSec, ID)

def createMDRefDMDSec(LABEL, itemdirectoryPath, directoryPathSTR):
    global globalDmdSecCounter
    globalDmdSecCounter += 1
    dmdSec = etree.Element("dmdSec")
    ID = "dmdSec_" + globalDmdSecCounter.__str__()
    dmdSec.set("ID", ID)
    XPTR = "xpointer(id("
    tree = etree.parse(itemdirectoryPath)
    root = tree.getroot()
    for item in root.findall("{http://www.loc.gov/METS/}dmdSec"):
        XPTR = "%s %s" % (XPTR, item.get("ID"))
    XPTR = XPTR.replace(" ", "'", 1) + "'))"
    newChild(dmdSec, "mdRef", text=None, sets=[("LABEL", LABEL), (xlinkBNS +"href", directoryPathSTR), ("MDTYPE", "OTHER"), ("LOCTYPE","OTHER"), ("OTHERLOCTYPE", "SYSTEM"), ("XPTR", XPTR)])
    return (dmdSec, ID)


def createTechMD(fileUUID):
    ret = etree.Element("techMD")
    techMD = ret #newChild(amdSec, "digiprovMD")
    #digiprovMD.set("ID", "digiprov-"+ os.path.basename(filename) + "-" + fileUUID)
    global globalTechMDCounter
    globalTechMDCounter += 1
    techMD.set("ID", "techMD_"+ globalTechMDCounter.__str__())

    mdWrap = newChild(techMD,"mdWrap")
    mdWrap.set("MDTYPE", "PREMIS:OBJECT")
    xmlData = newChild(mdWrap, "xmlData")
    #premis = etree.SubElement( xmlData, "premis", nsmap={None: premisNS}, \
    #    attrib = { "{" + xsiNS + "}schemaLocation" : "info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/premis.xsd" })
    #premis.set("version", "2.0")

    #premis = etree.SubElement( xmlData, "premis", attrib = {xsiBNS+"type": "premis:file"})

    sql = "SELECT fileSize, checksum FROM Files WHERE fileUUID = '%s';" % (fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        fileSize = row[0].__str__()
        checksum = row[1].__str__()
        row = c.fetchone()
    sqlLock.release()

    #OBJECT
    object = etree.SubElement(xmlData, "object", nsmap={None: premisNS})
    object.set( xsiBNS+"type", "file")
    object.set(xsiBNS+"schemaLocation", premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
    object.set("version", "2.2")

    objectIdentifier = etree.SubElement(object, "objectIdentifier")
    etree.SubElement(objectIdentifier, "objectIdentifierType").text = "UUID"
    etree.SubElement(objectIdentifier, "objectIdentifierValue").text = fileUUID

    #etree.SubElement(object, "objectCategory").text = "file"

    objectCharacteristics = etree.SubElement(object, "objectCharacteristics")
    etree.SubElement(objectCharacteristics, "compositionLevel").text = "0"

    fixity = etree.SubElement(objectCharacteristics, "fixity")
    etree.SubElement(fixity, "messageDigestAlgorithm").text = "sha256"
    etree.SubElement(fixity, "messageDigest").text = checksum

    etree.SubElement(objectCharacteristics, "size").text = fileSize

    sql = "SELECT formatName, formatVersion, formatRegistryName, formatRegistryKey FROM FilesIDs WHERE fileUUID = '%s';" % (fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    if not row:
        format = etree.SubElement(objectCharacteristics, "format")
        formatDesignation = etree.SubElement(format, "formatDesignation")
        etree.SubElement(formatDesignation, "formatName").text = "Unknown"
    while row != None:
        #print row
        format = etree.SubElement(objectCharacteristics, "format")
        #fileUUID = row[0]

        formatDesignation = etree.SubElement(format, "formatDesignation")
        etree.SubElement(formatDesignation, "formatName").text = row[0]
        etree.SubElement(formatDesignation, "formatVersion").text = row[1]

        formatRegistry = etree.SubElement(format, "formatRegistry")
        etree.SubElement(formatRegistry, "formatRegistryName").text = row[2]
        etree.SubElement(formatRegistry, "formatRegistryKey").text = row[3]
        row = c.fetchone()
    sqlLock.release()

    objectCharacteristicsExtension = etree.SubElement(objectCharacteristics, "objectCharacteristicsExtension")

    sql = "SELECT FPCommandOutput.content FROM FPCommandOutput \
           INNER JOIN fpr_fprule ON FPCommandOutput.ruleUUID = fpr_fprule.uuid \
           WHERE fileUUID = '{file}' AND purpose = 'characterize';".format(file=fileUUID)
    c, sqlLock = databaseInterface.querySQL(sql)
    parser = etree.XMLParser(remove_blank_text=True)
    for row in c:
        output = etree.XML(row[0], parser)
        objectCharacteristicsExtension.append(output)
    sqlLock.release()

    sql = "SELECT Files.originalLocation FROM Files WHERE Files.fileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    if not row:
        print >>sys.stderr, "Error: no location found."
    while row != None:
        etree.SubElement(object, "originalName").text = escape(row[0])
        row = c.fetchone()
    sqlLock.release()

    #Derivations
    sql = "SELECT sourceFileUUID, derivedFileUUID, relatedEventUUID FROM Derivations WHERE sourceFileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        relationship = etree.SubElement(object, "relationship")
        etree.SubElement(relationship, "relationshipType").text = "derivation"
        etree.SubElement(relationship, "relationshipSubType").text = "is source of"

        relatedObjectIdentification = etree.SubElement(relationship, "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, "relatedObjectIdentifierValue").text = row[1]

        relatedEventIdentification = etree.SubElement(relationship, "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, "relatedEventIdentifierValue").text = row[2]

        row = c.fetchone()
    sqlLock.release()

    sql = "SELECT sourceFileUUID, derivedFileUUID, relatedEventUUID FROM Derivations WHERE derivedFileUUID = '" + fileUUID + "';"
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        relationship = etree.SubElement(object, "relationship")
        etree.SubElement(relationship, "relationshipType").text = "derivation"
        etree.SubElement(relationship, "relationshipSubType").text = "has source"

        relatedObjectIdentification = etree.SubElement(relationship, "relatedObjectIdentification")
        etree.SubElement(relatedObjectIdentification, "relatedObjectIdentifierType").text = "UUID"
        etree.SubElement(relatedObjectIdentification, "relatedObjectIdentifierValue").text = row[0]

        relatedEventIdentification = etree.SubElement(relationship, "relatedEventIdentification")
        etree.SubElement(relatedEventIdentification, "relatedEventIdentifierType").text = "UUID"
        etree.SubElement(relatedEventIdentification, "relatedEventIdentifierValue").text = row[2]

        row = c.fetchone()
    sqlLock.release()
    return ret

def createDigiprovMD(fileUUID):
    ret = []
    #EVENTS
    
    #for #5379 - changed sql to limit premis events generated for email messages
    sql = """SELECT e.pk, e.fileUUID, e.eventIdentifierUUID, e.eventType, 
             e.eventDateTime, e.eventDetail, e.eventOutcome, 
             e.eventOutcomeDetailNote, e.linkingAgentIdentifier, 
             t.type, f.currentLocation 
             FROM Events e join Files f on e.fileUUID = f.fileUUID join 
             Transfers t on f.transferUUID = t.transferUUID  
             WHERE e.fileUUID = '{}' and ((t.type !='Maildir') or 
             (t.type ='Maildir' and f.currentLocation like '\%SIPDirectory\%objects/attachment%') 
             or (t.type='Maildir' and e.eventType = 'ingestion'))""".format(fileUUID)

    #sql = "SELECT pk, fileUUID, eventIdentifierUUID, eventType, eventDateTime, eventDetail, eventOutcome, eventOutcomeDetailNote, linkingAgentIdentifier FROM Events WHERE fileUUID = '" + fileUUID + "';"
    rows = databaseInterface.queryAllSQL(sql)
    for row in rows:
        digiprovMD = etree.Element("digiprovMD")
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        #digiprovMD.set("ID", "digiprov-"+ os.path.basename(filename) + "-" + fileUUID)
        global globalDigiprovMDCounter
        globalDigiprovMDCounter += 1
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())

        mdWrap = newChild(digiprovMD,"mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:EVENT")
        xmlData = newChild(mdWrap,"xmlData")
        event = etree.SubElement(xmlData, "event", nsmap={None: premisNS})
        event.set(xsiBNS+"schemaLocation", premisNS + " http://www.loc.gov/standards/premis/v2/premis-v2-2.xsd")
        event.set("version", "2.2")

        eventIdentifier = etree.SubElement(event, "eventIdentifier")
        etree.SubElement(eventIdentifier, "eventIdentifierType").text = "UUID"
        etree.SubElement(eventIdentifier, "eventIdentifierValue").text = row[2]

        etree.SubElement(event, "eventType").text = row[3]
        etree.SubElement(event, "eventDateTime").text = row[4].__str__().replace(" ", "T")
        etree.SubElement(event, "eventDetail").text = escape(row[5])

        eventOutcomeInformation  = etree.SubElement(event, "eventOutcomeInformation")
        etree.SubElement(eventOutcomeInformation, "eventOutcome").text = row[6]
        eventOutcomeDetail = etree.SubElement(eventOutcomeInformation, "eventOutcomeDetail")
        etree.SubElement(eventOutcomeDetail, "eventOutcomeDetailNote").text = escape(row[7])
        
        if row[8]:
            linkingAgentIdentifier = etree.SubElement(event, "linkingAgentIdentifier")
            etree.SubElement(linkingAgentIdentifier, "linkingAgentIdentifierType").text = "Archivematica user pk"
            etree.SubElement(linkingAgentIdentifier, "linkingAgentIdentifierValue").text = row[8].__str__()
        
        #linkingAgentIdentifier
        sql = """SELECT agentIdentifierType, agentIdentifierValue, agentName, agentType FROM Agents;"""
        c, sqlLock = databaseInterface.querySQL(sql)
        row = c.fetchone()
        while row != None:
            linkingAgentIdentifier = etree.SubElement(event, "linkingAgentIdentifier")
            etree.SubElement(linkingAgentIdentifier, "linkingAgentIdentifierType").text = row[0]
            etree.SubElement(linkingAgentIdentifier, "linkingAgentIdentifierValue").text = row[1]
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
        digiprovMD = etree.Element("digiprovMD")
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        mdWrap = newChild(digiprovMD,"mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:AGENT")
        xmlData = newChild(mdWrap,"xmlData")
        #agents = etree.SubElement(xmlData, "agents")
        xmlData.append(createAgent(row[0], row[1], row[2], row[3]))
        row = c.fetchone()
    sqlLock.release()
    
    sql = """SELECT auth_user.id, auth_user.username, auth_user.first_name, auth_user.last_name FROM SIPs JOIN Files ON SIPs.sipUUID = Files.sipUUID JOIN Events ON Files.fileUUID = Events.fileUUID JOIN auth_user ON Events.linkingAgentIdentifier = auth_user.id WHERE SIPs.sipUUID = '%s' GROUP BY auth_user.id;""" % (fileGroupIdentifier)
    c, sqlLock = databaseInterface.querySQL(sql)
    row = c.fetchone()
    while row != None:
        globalDigiprovMDCounter += 1
        digiprovMD = etree.Element("digiprovMD")
        digiprovMD.set("ID", "digiprovMD_"+ globalDigiprovMDCounter.__str__())
        ret.append(digiprovMD) #newChild(amdSec, "digiprovMD")
        mdWrap = newChild(digiprovMD,"mdWrap")
        mdWrap.set("MDTYPE", "PREMIS:AGENT")
        xmlData = newChild(mdWrap,"xmlData")
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
    AMD = etree.Element("amdSec")
    AMD.set("ID", AMDID)
    ret = (AMD, AMDID)
    #tech MD
    #digiprob MD
    AMD.append(createTechMD(fileUUID))

    if use == "original":
        metadataAppliesToList = [(fileUUID, FileMetadataAppliesToType), (fileGroupIdentifier, SIPMetadataAppliesToType), (transferUUID.__str__(), TransferMetadataAppliesToType)]
        for a in archivematicaGetRights(metadataAppliesToList, fileUUID):
            globalRightsMDCounter +=1
            rightsMD = etree.SubElement(AMD, "rightsMD")
            rightsMD.set("ID", "rightsMD_" + globalRightsMDCounter.__str__())
            mdWrap = newChild(rightsMD,"mdWrap")
            mdWrap.set("MDTYPE", "PREMIS:RIGHTS")
            xmlData = newChild(mdWrap, "xmlData")
            xmlData.append(a)

        if typeOfTransfer == "Dspace":
            for a in archivematicaCreateMETSRightsDspaceMDRef(fileUUID, filePath, transferUUID, itemdirectoryPath):
                globalRightsMDCounter +=1
                rightsMD = etree.SubElement(AMD, "rightsMD")
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
            structMap = root.find(metsBNS + "structMap")
            id = structMap.get("ID")
            if not id:
                structMap.set("ID", "structMap_2")
            ret.append(structMap)
            for item in structMap.findall(".//" + metsBNS + "fptr"):
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
def createFileSec(directoryPath, structMapDiv):
    global fileNameToFileID
    global trimStructMap
    global trimStructMapObjects
    global globalDmdSecCounter
    global globalAmdSecCounter
    global globalDigiprovMDCounter
    global dmdSecs
    global amdSecs
    
    
    delayed = []
    filesInThisDirectory = []
    dspaceMetsDMDID = None
    directoryContents = os.listdir(directoryPath)
    directoryContentsTuples = []
    for item in directoryContents:
        itemdirectoryPath = os.path.join(directoryPath, item)
        if os.path.isdir(itemdirectoryPath):
            delayed.append(item)

        elif os.path.isfile(itemdirectoryPath):
            #find original file name
            directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath, baseDirectoryPathString, 1)
            sql = """SELECT Related.originalLocation AS 'derivedFromOriginalLocation', 
                            Current.originalLocation
                        FROM Files AS Current 
                        LEFT OUTER JOIN Derivations ON Current.fileUUID = Derivations.derivedFileUUID 
                        LEFT OUTER JOIN Files AS Related ON Derivations.sourceFileUUID = Related.fileUUID
                        WHERE Current.removedTime = 0 AND Current.%s = '%s' 
                            AND Current.currentLocation = '%s';""" % (fileGroupType, fileGroupIdentifier, MySQLdb.escape_string(directoryPathSTR))
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            if row == None:
                print >>sys.stderr, "No uuid for file: \"", directoryPathSTR, "\""
                sharedVariablesAcrossModules.globalErrorCount += 1
                sqlLock.release()
                continue
            while row != None:
                #add to files in this directory tuple list
                derivedFromOriginalName = row[0]
                originalLocation = row[1]
                if derivedFromOriginalName != None:
                    originalLocation = derivedFromOriginalName
                originalName = os.path.basename(originalLocation) + u"/" #+ u"/" keeps normalized after original / is very uncommon in a file name
                directoryContentsTuples.append((originalName, item,)) 
                row = c.fetchone()
            sqlLock.release()
            
    #order files by their original name
    for originalName, item in sorted(directoryContentsTuples, key=lambda listItems: listItems[0], cmp=sharedVariablesAcrossModules.collator.compare):
        #item = unicode(item)
        itemdirectoryPath = os.path.join(directoryPath, item)
            
        #myuuid = uuid.uuid4()
        myuuid=""
        DMDIDS=""
        #directoryPathSTR = itemdirectoryPath.replace(baseDirectoryPath + "objects", "objects", 1)
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

        if typeOfTransfer == "TRIM" and trimStructMap == None:
            trimStructMap = etree.Element("structMap", attrib={"TYPE":"logical", "ID":"structMap_2", "LABEL":"Hierarchical arrangement"})
            trimStructMapObjects = etree.SubElement(trimStructMap, "div", attrib={"TYPE":"File", "LABEL":"objects"})
            
            trimDmdSec = getTrimDmdSec(baseDirectoryPath, fileGroupIdentifier)
            globalDmdSecCounter += 1
            dmdSecs.append(trimDmdSec)
            ID = "dmdSec_" + globalDmdSecCounter.__str__()
            trimDmdSec.set("ID", ID)
            trimStructMapObjects.set("DMDID", ID)
            
            # ==
            
            trimAmdSec = etree.Element("amdSec")
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
        fileDiv = etree.SubElement(structMapDiv, "div", LABEL=label, TYPE='Item')
        etree.SubElement(fileDiv, 'fptr', FILEID=fileId)
        fileNameToFileID[item] = fileId

        GROUPID = ""
        if fileGrpUUID:
            GROUPID = "Group-%s" % (fileGrpUUID)
            if use == "TRIM file metadata":
                use = "metadata"
            
        elif  use == "original" or use == "submissionDocumentation" or use == "metadata" or use == "maildirFile":
            GROUPID = "Group-%s" % (myuuid)
            if use == "maildirFile":
                use = "original"
            if use == "original":
                DMDIDS = createDMDIDSFromCSVParsedMetadataFiles(originalLocation.replace('%transferDirectory%', "", 1))
                if DMDIDS:
                    fileDiv.set("DMDID", DMDIDS)
                if typeOfTransfer == "TRIM":
                    trimFileDiv = etree.SubElement(trimStructMapObjects, "div", attrib={"TYPE":"Item"})
                    
                    trimFileDmdSec = getTrimFileDmdSec(baseDirectoryPath, fileGroupIdentifier, myuuid)
                    globalDmdSecCounter += 1
                    dmdSecs.append(trimFileDmdSec)
                    ID = "dmdSec_" + globalDmdSecCounter.__str__()
                    trimFileDmdSec.set("ID", ID)
                    
                    trimFileDiv.set("DMDID", ID)       
                    
                    etree.SubElement(trimFileDiv, "fptr", FILEID=fileId)

        elif use == "preservation":
            sql = "SELECT * FROM Derivations WHERE derivedFileUUID = '" + myuuid + "';"
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            while row != None:
                GROUPID = "Group-%s" % (row[1])
                row = c.fetchone()
            sqlLock.release()

        elif use == "license" or use == "text/ocr" or use == "DSPACEMETS":
            sql = """SELECT fileUUID FROM Files WHERE removedTime = 0 AND %s = '%s' AND fileGrpUse = 'original' AND originalLocation LIKE '%s/%%'""" % (fileGroupType, fileGroupIdentifier, MySQLdb.escape_string(os.path.dirname(originalLocation)).replace("%", "\%"))
            c, sqlLock = databaseInterface.querySQL(sql)
            row = c.fetchone()
            while row != None:
                GROUPID = "Group-%s" % (row[0])
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
            file = etree.SubElement(globalFileGrps[use], "file", ID=fileId, GROUPID=GROUPID)
            if use == "original":
                filesInThisDirectory.append(file)
            #<Flocat xlink:href="objects/file1-UUID" locType="other" otherLocType="system"/>
            newChild(file, "FLocat", sets=[(xlinkBNS +"href",directoryPathSTR), ("LOCTYPE","OTHER"), ("OTHERLOCTYPE", "SYSTEM")])
            if includeAmdSec:
                AMD, ADMID = getAMDSec(myuuid, directoryPathSTR, use, fileGroupType, fileGroupIdentifier, transferUUID, itemdirectoryPath, typeOfTransfer)
                amdSecs.append(AMD)
                file.set("ADMID", ADMID)


    if dspaceMetsDMDID != None:
        for file in filesInThisDirectory:
            file.set("DMDID", dspaceMetsDMDID)
    
    for item in sorted(delayed, cmp=sharedVariablesAcrossModules.collator.compare):
        itemdirectoryPath = os.path.join(directoryPath, item)
        directoryDiv = newChild(structMapDiv, "div", sets=[("TYPE","Directory"), ("LABEL",item)])
        DMDIDS = createDMDIDSFromCSVParsedMetadataDirectories(itemdirectoryPath.replace(baseDirectoryPath, "", 1))
        if DMDIDS:
            directoryDiv.set("DMDID", DMDIDS)
        createFileSec(itemdirectoryPath, directoryDiv)
        
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

def create_object_metadata(label):
    source_md_counter = 1

    el = etree.Element('amdSec', {'ID': label})
    transfer_metadata_path = os.path.join(baseDirectoryPath, "objects/metadata/transfers")

    transfer, source = find_source_metadata(transfer_metadata_path)

    for filename in transfer:
        sourcemd = etree.SubElement(el, 'sourceMD', {'ID': 'sourceMD_{}'.format(source_md_counter)})
        mdwrap = etree.SubElement(sourcemd, 'mdWrap', {'MDTYPE': 'OTHER'})
        xmldata = etree.SubElement(mdwrap, 'xmlData')
        source_md_counter += 1
        parser = etree.XMLParser(remove_blank_text=True)
        md = etree.parse(filename, parser)
        xmldata.append(md.getroot())

    for filename in source:
        sourcemd = etree.SubElement(el, 'sourceMD', {'ID': 'sourceMD_{}'.format(source_md_counter)})
        source_md_counter += 1
        attributes = {
            xlinkBNS + 'href': os.path.relpath(filename, baseDirectoryPath),
            'MDTYPE': 'OTHER',
            'LOCTYPE': 'OTHER',
            'OTHERLOCTYPE': 'SYSTEM'
        }
        etree.SubElement(sourcemd, 'mdRef', attributes)

    return el


if __name__ == '__main__':
    sharedVariablesAcrossModules.collator = PyICU.Collator.createInstance(PyICU.Locale(opts.PyICULocale))
    while False: #used to stall the mcp and stop the client for testing this module
        import time
        time.sleep(10)

    parseMetadata(baseDirectoryPath)

    if not baseDirectoryPath.endswith('/'):
        baseDirectoryPath += '/'
    structMap = etree.Element("structMap")
    structMap.set("TYPE", "physical")
    structMap.set("ID", "structMap_1")
    structMap.set("LABEL", "Archivematica default")
    structMapDiv = newChild(structMap, "div", sets=[("TYPE","Directory"), ("LABEL",os.path.basename(baseDirectoryPath[:-1]))])

    structMapDiv = newChild(structMapDiv, "div", sets=[("TYPE","Directory"), ("LABEL","objects"), ("ADMID","amdSec_1") ])
    amdSecs.append(create_object_metadata('amdSec_1'))

    createFileSec(os.path.join(baseDirectoryPath, "objects"), structMapDiv)


    fileSec = etree.Element( "fileSec")
    for group in globalFileGrpsUses: #globalFileGrps.itervalues():
        grp = globalFileGrps[group]
        if len(grp) > 0:
            fileSec.append(grp)

    rootNSMap = {None: metsNS}
    rootNSMap.update(NSMAP)
    root = etree.Element( "mets", \
    nsmap = rootNSMap, \
    attrib = { "{" + xsiNS + "}schemaLocation" : "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version18/mets.xsd" } )
    etree.SubElement(root,"metsHdr").set("CREATEDATE", databaseInterface.getUTCDate().split(".")[0])



    dc = createDublincoreDMDSecFromDBData(SIPMetadataAppliesToType, fileGroupIdentifier)
    if dc != None:
        (dmdSec, ID) = dc
        structMapDiv.set("DMDID", ID)
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
