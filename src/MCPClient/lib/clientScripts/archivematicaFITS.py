#!/usr/bin/env python2

import sys
import shlex
import lxml.etree as etree
import uuid
import subprocess
import os

# archivematicaCommon
from archivematicaFunctions import getTagged
from archivematicaFunctions import escapeForCommand
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoFPCommandOutput
from databaseFunctions import insertIntoEvents
import databaseInterface

# initialize Django (required for Django 1.7)
import django
django.setup()

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


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.FITS")

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

    sql = """SELECT fileUUID FROM FPCommandOutput WHERE fileUUID = %s;"""
    if len(databaseInterface.queryAllSQL(sql, (fileUUID,))):
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

    except OSError as ose:
        print >>sys.stderr, "Execution failed:", ose
        exit(1)
    exit(exitCode)
