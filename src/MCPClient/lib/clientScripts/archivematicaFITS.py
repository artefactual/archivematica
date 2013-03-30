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
# @author Joseph Perry <joseph@artefactual.com>
import sys
import shlex
import lxml.etree as etree
import uuid
import subprocess
import os
import uuid

from createXmlEventsAssist import createEvent
from createXmlEventsAssist import createOutcomeInformation
from createXmlEventsAssist import createLinkingAgentIdentifier
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivematicaFunctions import getTagged
from archivematicaFunctions import escapeForCommand
from databaseFunctions import insertIntoFilesFits
from databaseFunctions import insertIntoEvents
from databaseFunctions import insertIntoFilesIDs
import databaseInterface

databaseInterface.printSQL = False
excludeJhoveProperties = True
formats = []
FITSNS = "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}"



def parseIdsSimple(FITS_XML, fileUUID):
    #simpleIdPlaces = [(table, tool, iter)]
    simpleIdPlaces = [
        ("FileIDsByFitsDROIDMimeType", "Droid", "{http://www.nationalarchives.gov.uk/pronom/FileCollection}MimeType"),
        ("FITS DROID PUID", "Droid", "{http://www.nationalarchives.gov.uk/pronom/FileCollection}PUID"),
        ("FileIDsByFitsFfidentMimetype", "ffident", "mimetype"),
        ("FileIDsByFitsFileUtilityMimetype", "file utility", "mimetype"),
        ("FileIDsByFitsFileUtilityFormat", "file utility", "format"),
        ("FileIDsByFitsJhoveMimeType", "Jhove", "{}mimeType"),
        ("FileIDsByFitsJhoveFormat", "Jhove", "{}format")
        
    ]
    
    for toolKey, tool, iterOn in simpleIdPlaces:
        identified = []
        fileIDs = []
        for element in FITS_XML.iter("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}tool"):
            if element.get("name") == tool:
                toolVersion = element.get("version")
                for element2 in element.getiterator(iterOn):
                    if element2.text != None:
                        if element2.text in identified:
                            continue
                        identified.append(element2.text)
                        sql = """SELECT fileID FROM FileIDsBySingleID WHERE tool = '%s' AND toolVersion='%s' AND id = '%s' AND FileIDsBySingleID.enabled = TRUE;""" % (toolKey, toolVersion, element2.text)
                        fileIDS = databaseInterface.queryAllSQL(sql)
                        if not fileIDS:
                            print "No Archivematica entry found for:", toolKey, toolVersion, element2.text
                        for fileID in fileIDS:
                            sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', '%s');""" % (fileUUID, fileID[0])
                            databaseInterface.runSQL(sql)
        if fileIDs == [] and False:
            print >>sys.stderr, "No archivematica id for: ", tool, iterOn, element2.text
                
                
    for element in FITS_XML.findall(".//{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}identity[@mimetype]"):
        format = element.get("mimetype")
        if format:
            sql = """SELECT FileIDsBySingleID.fileID, FileIDs.fileIDType, FileIDsBySingleID.id FROM FileIDsBySingleID JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk WHERE FileIDs.fileIDType = 'c26227f7-fca8-4d98-9d8e-cfab86a2dd0a' AND FileIDsBySingleID.id = '%s' AND FileIDsBySingleID.enabled = TRUE AND FileIDs.enabled = TRUE;""" % (format)
            fileIDS = databaseInterface.queryAllSQL(sql)
            for fileID in fileIDS:
                sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', '%s');""" % (fileUUID, fileID[0])
                databaseInterface.runSQL(sql)
    for element in FITS_XML.findall(".//{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}identity[@format]"):
        format = element.get("format")
        if format:
            sql = """SELECT FileIDsBySingleID.fileID, FileIDs.fileIDType, FileIDsBySingleID.id FROM FileIDsBySingleID JOIN FileIDs ON FileIDsBySingleID.fileID = FileIDs.pk WHERE FileIDs.fileIDType = 'b0bcccfb-04bc-4daa-a13c-77c23c2bda85' AND FileIDsBySingleID.id = '%s' AND FileIDsBySingleID.enabled = TRUE AND FileIDs.enabled = TRUE;""" % (format)
            fileIDS = databaseInterface.queryAllSQL(sql)
            for fileID in fileIDS:
                sql = """INSERT INTO FilesIdentifiedIDs (fileUUID, fileID) VALUES ('%s', '%s');""" % (fileUUID, fileID[0])
                databaseInterface.runSQL(sql)
            
def excludeJhoveProperties(fits):
    """Exclude <properties> from <fits><toolOutput><tool name="Jhove" version="1.5"><repInfo> because that field contains unnecessary excess data and the key data are covered by output from other FITS tools."""
    prefix = ""
    formatValidation = None
    #print fits
    #print etree.tostring(fits, pretty_print=True)

    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Jhove":
            formatValidation = tool
            break
    if formatValidation == None:
        print >>sys.stderr, "No format validation tool (Jhove)."
        return fits
    repInfo = getTagged(formatValidation, "repInfo")[0]
    properties = getTagged(repInfo, "properties")

    if len(properties):
        repInfo.remove(properties[0])
    return fits


def formatValidationFITSAssist(fits):
    prefix = ""
    formatValidation = None

    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Jhove":
            formatValidation = tool
            break
    if formatValidation == None:
        print >>sys.stderr, "No format validation tool (Jhove)."
        quit(3)

    repInfo = getTagged(formatValidation, "repInfo")[0]
    #<eventDetail>program="DROID"; version="3.0"</eventDetail>
    eventDetailText =   "program=\"" + formatValidation.get("name") \
                        + "\"; version=\"" + formatValidation.get("version") + "\""


    #<status>Well-Formed and valid</status>
    status = getTagged( repInfo, prefix + "status")[0].text
    eventOutcomeText = "fail"
    if status == "Well-Formed and valid":
        eventOutcomeText = "pass"

    #<eventOutcomeDetailNote> format="Windows Bitmap"; version="3.0"; result="Well-formed and valid" </eventOutcomeDetailNote>
    format = getTagged(repInfo, prefix + "format")[0].text
    versionXML = getTagged(repInfo, prefix + "version")
    version = ""
    if len(versionXML):
        version = versionXML[0].text
    eventOutcomeDetailNote = "format=\"" + format
    if version:
        eventOutcomeDetailNote += "\"; version=\"" + version
    eventOutcomeDetailNote += "\"; result=\"" + status + "\""

    return tuple([eventDetailText, eventOutcomeText, eventOutcomeDetailNote]) #tuple([1, 2, 3]) returns (1, 2, 3).


def formatIdentificationFITSAssist(fits, fileUUID):
    prefix = "{http://www.nationalarchives.gov.uk/pronom/FileCollection}"
    formatIdentification = None

    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Droid":
            formatIdentification = tool
            break
    #<eventDetail>program="DROID"; version="3.0"</eventDetail>
    eventDetailText =   "program=\"" + formatIdentification.get("name") \
                        + "\"; version=\"" + formatIdentification.get("version") + "\""

    #<eventOutcome>positive</eventOutcome>

    fileCollection = getTagged(formatIdentification, prefix + "FileCollection")[0]
    IdentificationFile = getTagged(fileCollection, prefix + "IdentificationFile")[0]
    eventOutcomeText =  IdentificationFile.get( "IdentQuality")

    #<eventOutcomeDetailNote>fmt/116</eventOutcomeDetailNote>
    #<FileFormatHit />
    fileFormatHits = getTagged(IdentificationFile, prefix + "FileFormatHit")
    eventOutcomeDetailNotes = []
    eventOutcomeDetailNote = ""
    for fileFormatHit in fileFormatHits:
        format = etree.Element("format")
        if len(fileFormatHit):
            formatIDSQL = {"fileUUID":fileUUID, \
                        "formatName":"", \
                        "formatVersion":"", \
                        "formatRegistryName":"PRONOM", \
                        "formatRegistryKey":""}
            eventOutcomeDetailNote = getTagged(fileFormatHit, prefix + "PUID")[0].text

            #formatDesignation = etree.SubElement(format, "formatDesignation")
            formatName = getTagged(fileFormatHit, prefix + "Name")
            formatVersion = getTagged(fileFormatHit, prefix + "Version")


            if len(formatName):
                #etree.SubElement(formatDesignation, "formatName").text = formatName[0].text
                formatIDSQL["formatName"] = formatName[0].text
            if len(formatVersion):
                #etree.SubElement(formatDesignation, "formatVersion").text = formatVersion[0].text
                formatIDSQL["formatVersion"] = formatVersion[0].text
            formatRegistry = etree.SubElement(format, "formatRegistry")

            PUID = getTagged(fileFormatHit, prefix + "PUID")
            if len(PUID):
                #etree.SubElement(formatRegistry, "formatRegistryName").text = "PRONOM"
                #etree.SubElement(formatRegistry, "formatRegistryKey").text = PUID[0].text
                formatIDSQL["formatRegistryKey"] = PUID[0].text
            formats.append(format)
            print formatIDSQL
            insertIntoFilesIDs(fileUUID=fileUUID, \
                               formatName=formatIDSQL["formatName"], \
                               formatVersion=formatIDSQL["formatVersion"], \
                               formatRegistryName=formatIDSQL["formatRegistryName"], \
                               formatRegistryKey=formatIDSQL["formatRegistryKey"])
        else:
            eventOutcomeDetailNote = "No Matching Format Found"
            formatDesignation = etree.SubElement(format, "formatDesignation")
            etree.SubElement(formatDesignation, "formatName").text = "Unknown"
            formats.append(format)
        eventOutcomeDetailNotes.append(eventOutcomeDetailNote)
    return tuple([eventDetailText, eventOutcomeText, eventOutcomeDetailNotes]) #tuple([1, 2, 3]) returns (1, 2, 3).


def includeFits(fits, xmlFile, date, eventUUID, fileUUID):
    global exitCode
    ##eventOutcome = createOutcomeInformation( eventOutcomeDetailNote = uuid)
    #TO DO... Gleam the event outcome information from the output

    #print etree.tostring(fits, pretty_print=True)
    #</CREATE formatIdentificationFITSAssist EVENTS>
    #try:
    eventDetailText, eventOutcomeText, eventOutcomeDetailNotes = formatIdentificationFITSAssist(fits, fileUUID)
    #except:
    if 0:
        eventDetailText = "Failed"
        eventOutcomeText = "Failed"
        eventOutcomeDetailNotes = ["Failed"]
        exitCode += 4
    outcomeInformation = createOutcomeInformation( "To be removed", eventOutcomeText)
    #formatIdentificationEvent = createEvent( eventUUID, "format identification", \
    #                                         eventDateTime=date, \
    #                                         eventDetailText=eventDetailText, \
    #                                         eOutcomeInformation=outcomeInformation)

    #eventOutcomeInformation = getTagged(formatIdentificationEvent, "eventOutcomeInformation")[0]
    #eventOutcomeDetail = getTagged(eventOutcomeInformation, "eventOutcomeDetail")[0]
    #eventOutcomeInformation.remove(eventOutcomeDetail)

    for eventOutcomeDetailNote in eventOutcomeDetailNotes:
        #eventOutcomeDetail = etree.SubElement(eventOutcomeInformation, "eventOutcomeDetail")
        #etree.SubElement(eventOutcomeDetail, "eventOutcomeDetailNote").text = eventOutcomeDetailNote

        insertIntoEvents(fileUUID=fileUUID, \
                         eventIdentifierUUID=uuid.uuid4().__str__(), \
                         eventType="format identification", \
                         eventDateTime=date, \
                         eventDetail=eventDetailText, \
                         eventOutcome=eventOutcomeText, \
                         eventOutcomeDetailNote=eventOutcomeDetailNote)

    #</CREATE formatIdentificationFITSAssist EVENTS>
    try:
        eventDetailText, eventOutcomeText, eventOutcomeDetailNote = formatValidationFITSAssist(fits)
    except:
        eventDetailText = "Failed"
        eventOutcomeText = "Failed"
        eventOutcomeDetailNotes = "Failed"
        exitCode += 3
    #outcomeInformation = createOutcomeInformation( eventOutcomeDetailNote, eventOutcomeText)
    #formatValidationEvent = createEvent( uuid.uuid4().__str__(), "validation", \
    #                                         eventDateTime=date, \
    #                                         eventDetailText=eventDetailText, \
    #                                         eOutcomeInformation=outcomeInformation)
    insertIntoEvents(fileUUID=fileUUID, \
                     eventIdentifierUUID=uuid.uuid4().__str__(), \
                     eventType="validation", \
                     eventDateTime=date, \
                     eventDetail=eventDetailText, \
                     eventOutcome=eventOutcomeText, \
                     eventOutcomeDetailNote=eventOutcomeDetailNote)

    #tree = etree.parse( xmlFile )
    #root = tree.getroot()

    #events = getTagged(root, "events")[0]
    #events.append(formatIdentificationEvent)
    #events.append(formatValidationEvent)

    #objectCharacteristics = getTagged(getTagged(root, "object")[0], "objectCharacteristics")[0]
    #for format in formats:
    #    objectCharacteristics.append(format)
    #objectCharacteristicsExtension = etree.SubElement(objectCharacteristics, "objectCharacteristicsExtension")
    #objectCharacteristicsExtension.append(fits)



    #tree = etree.ElementTree(root)
    #tree.write(xmlFile)

if __name__ == '__main__':
    global exitCode
    exitCode = 0
    target = sys.argv[1]
    XMLfile = sys.argv[2]
    date = sys.argv[3]
    eventUUID = sys.argv[4]
    fileUUID  = sys.argv[5]
    fileGrpUse = sys.argv[6]

    if fileGrpUse in ["DSPACEMETS", "maildirFile"]:
        print "file's fileGrpUse in exclusion list, skipping"
        exit(0)

    sql = """SELECT fileUUID FROM FilesFits WHERE fileUUID = '%s';""" % (fileUUID)
    if len(databaseInterface.queryAllSQL(sql)):
        print >>sys.stderr, "Warning: Fits has already run on this file. Not running again."
        exit(0)

    tempFile="/tmp/" + uuid.uuid4().__str__()

    command = "openfits -i \"" + escapeForCommand(target) + "\" -o \"" + tempFile + "\""
    #print >>sys.stderr, command
    #print >>sys.stderr,  shlex.split(command)
    try:
        p = subprocess.Popen(shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #p.wait()
        output = p.communicate()
        retcode = p.returncode

        if output[0] != "":
            print output[0]
        if output[1] != "":
            print >>sys.stderr, output[1]

        #it executes check for errors
        if retcode != 0:
            print >>sys.stderr, "error code:" + retcode.__str__()
            print output[1]# sError
            #return retcode
            quit(retcode)
        try:
            tree = etree.parse(tempFile)
        except:
            os.remove(tempFile)
            print >>sys.stderr, "Failed to read Fits's xml."
            exit(2)
        fits = tree.getroot()
        os.remove(tempFile)
        #fits = etree.XML(output[0])
        if excludeJhoveProperties:
            fits = excludeJhoveProperties(fits)
        insertIntoFilesFits(fileUUID, etree.tostring(fits, pretty_print=False))
        includeFits(fits, XMLfile, date, eventUUID, fileUUID)
        parseIdsSimple(fits, fileUUID)

    except OSError, ose:
        print >>sys.stderr, "Execution failed:", ose
        #return 1
        exit(1)
    exit(exitCode)
