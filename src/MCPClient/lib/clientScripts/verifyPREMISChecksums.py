#!/usr/bin/env python2

import sys
from optparse import OptionParser

import django
django.setup()

# dashboard
from main.models import File

# archivematicaCommon
from custom_handlers import get_script_logger
import databaseFunctions
from externals.checksummingTools import get_file_checksum

def verifyChecksum(fileUUID, filePath, date, eventIdentifierUUID):
    f = File.objects.get(uuid=fileUUID)

    if f.checksum in ('', 'None'):
        print >>sys.stderr, 'No checksum found in database for file:', fileUUID, filePath
        exit(1)

    checksumFile = get_file_checksum(filePath, f.checksumtype)

    eventOutcome = ''
    eventOutcomeDetailNote = ''
    exitCode = 0

    if checksumFile != f.checksum:
        eventOutcomeDetailNote = str(checksumFile) + ' != ' + f.checksum
        eventOutcome = 'Fail'
        exitCode = 2
        print >>sys.stderr, 'Checksums do not match:', fileUUID, filePath
        print >>sys.stderr, eventOutcomeDetailNote
    else:
        eventOutcomeDetailNote = '%s %s' % (str(checksumFile), 'verified')
        eventOutcome = 'Pass'
        exitCode = 0

    databaseFunctions.insertIntoEvents(
        fileUUID=fileUUID,
        eventIdentifierUUID=eventIdentifierUUID,
        eventType='fixity check',
        eventDateTime=date,
        eventOutcome=eventOutcome,
        eventOutcomeDetailNote=eventOutcomeDetailNote,
        eventDetail='program="python"; module="hashlib.{}()"'.format(f.checksumtype)
    )

    exit(exitCode)


if __name__ == '__main__':
    logger = get_script_logger('archivematica.mcp.client.verifyPREMISChecksums')

    parser = OptionParser()
    parser.add_option('-i', '--fileUUID', action='store', dest='fileUUID', default='')
    parser.add_option('-p', '--filePath', action='store', dest='filePath', default='')
    parser.add_option('-d', '--date', action='store', dest='date', default='')
    parser.add_option('-u', '--eventIdentifierUUID', action='store', dest='eventIdentifierUUID', default='')
    (opts, args) = parser.parse_args()

    verifyChecksum(opts.fileUUID, opts.filePath, opts.date, opts.eventIdentifierUUID)
