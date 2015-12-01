#!/usr/bin/env python2

from optparse import OptionParser

# fileOperations requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import updateSizeAndChecksum

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.updateSizeAndChecksum")

    parser = OptionParser()
    parser.add_option("-i", "--fileUUID", action="store", dest="fileUUID", default="")
    parser.add_option("-p", "--filePath", action="store", dest="filePath", default="")
    parser.add_option("-d", "--date", action="store", dest="date", default="")
    parser.add_option("-u", "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    (opts, args) = parser.parse_args()

    updateSizeAndChecksum(opts.fileUUID, opts.filePath, opts.date, opts.eventIdentifierUUID)
