#!/usr/bin/env python2

from optparse import OptionParser

# databaseFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from databaseFunctions import insertIntoEvents


if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.createEvent")

    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-t",  "--eventType",        action="store", dest="eventType", default="")
    parser.add_option("-d",  "--eventDateTime",     action="store", dest="eventDateTime", default="")
    parser.add_option("-e",  "--eventDetail",       action="store", dest="eventDetail", default="")
    parser.add_option("-o",  "--eventOutcome",      action="store", dest="eventOutcome", default="")
    parser.add_option("-n",  "--eventOutcomeDetailNote",   action="store", dest="eventOutcomeDetailNote", default="")
    parser.add_option("-u",  "--eventIdentifierUUID",      action="store", dest="eventIdentifierUUID", default="")


    (opts, args) = parser.parse_args()

    insertIntoEvents(fileUUID=opts.fileUUID, \
                     eventIdentifierUUID=opts.eventIdentifierUUID, \
                     eventType=opts.eventType, \
                     eventDateTime=opts.eventDateTime, \
                     eventDetail=opts.eventDetail, \
                     eventOutcome=opts.eventOutcome, \
                     eventOutcomeDetailNote=opts.eventOutcomeDetailNote)
