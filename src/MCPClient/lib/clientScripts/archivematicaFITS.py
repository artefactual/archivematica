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

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from archivematicaFunctions import getTagged
from archivematicaFunctions import escapeForCommand
from databaseFunctions import insertIntoFPCommandOutput
from databaseFunctions import insertIntoEvents
import databaseInterface

databaseInterface.printSQL = False
excludeJhoveProperties = True
formats = []
FITSNS = "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}"

            
def excludeJhoveProperties(fits):
    """Exclude <properties> from <fits><toolOutput><tool name="Jhove" version="1.5"><repInfo> because that field contains unnecessary excess data and the key data are covered by output from other FITS tools."""
    formatValidation = None

    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Jhove":
            formatValidation = tool
            break
    if formatValidation == None:
        return fits
    repInfo = getTagged(formatValidation, "repInfo")[0]
    properties = getTagged(repInfo, "properties")

    if len(properties):
        repInfo.remove(properties[0])
    return fits


def formatValidationFITSAssist(fits):
    global exitCode
    prefix = ""
    formatValidation = None

    tools = getTagged(getTagged(fits, FITSNS + "toolOutput")[0], FITSNS + "tool")
    for tool in tools:
        if tool.get("name") == "Jhove":
            formatValidation = tool
            break
    if formatValidation == None:
        print >>sys.stderr, "No format validation tool output (Jhove)."
        exitCode += 6
        raise Exception('Jhove', 'not present')

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


def includeFits(fits, xmlFile, date, eventUUID, fileUUID):
    global exitCode
    #TO DO... Gleam the event outcome information from the output

    try:
        eventDetailText, eventOutcomeText, eventOutcomeDetailNote = formatValidationFITSAssist(fits)
    except:
        eventDetailText = "Failed"
        eventOutcomeText = "Failed"
        eventOutcomeDetailNote = "Failed"
        exitCode += 3
    insertIntoEvents(fileUUID=fileUUID, \
                     eventIdentifierUUID=uuid.uuid4().__str__(), \
                     eventType="validation", \
                     eventDateTime=date, \
                     eventDetail=eventDetailText, \
                     eventOutcome=eventOutcomeText, \
                     eventOutcomeDetailNote=eventOutcomeDetailNote)

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

    sql = """SELECT fileUUID FROM FPCommandOutput WHERE fileUUID = '%s';""" % (fileUUID)
    if len(databaseInterface.queryAllSQL(sql)):
        print >>sys.stderr, "Warning: Fits has already run on this file. Not running again."
        exit(0)

    tempFile="/tmp/" + uuid.uuid4().__str__()

    command = "fits.sh -i \"" + escapeForCommand(target) + "\" -o \"" + tempFile + "\""
    try:
        p = subprocess.Popen(shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
            quit(retcode)
        try:
            tree = etree.parse(tempFile)
        except:
            os.remove(tempFile)
            print >>sys.stderr, "Failed to read Fits's xml."
            exit(2)
        fits = tree.getroot()
        os.remove(tempFile)
        if excludeJhoveProperties:
            fits = excludeJhoveProperties(fits)
        # NOTE: This is hardcoded for now because FPCommandOutput references FPRule for future development,
        #       when characterization will become user-configurable and be decoupled from FITS specifically.
        #       Thus a stub rule must exist for FITS; this will be replaced with a real rule in the future.
        insertIntoFPCommandOutput(fileUUID, etree.tostring(fits, pretty_print=False), '3a19de70-0e42-4145-976b-3a248d43b462')
        includeFits(fits, XMLfile, date, eventUUID, fileUUID)

    except OSError, ose:
        print >>sys.stderr, "Execution failed:", ose
        exit(1)
    exit(exitCode)
