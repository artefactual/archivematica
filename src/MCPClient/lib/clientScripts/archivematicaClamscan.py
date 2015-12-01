#!/usr/bin/env python2

import os
import sys

import django
django.setup()
# dashboard
from main.models import Event

# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun
from databaseFunctions import insertIntoEvents

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.clamscan")
    fileUUID = sys.argv[1]
    target = sys.argv[2]
    date = sys.argv[3]
    taskUUID = sys.argv[4]

    # Check if scan event already exists for this file - if so abort early
    count = Event.objects.filter(file_uuid_id=fileUUID, event_type='virus check').count()
    if count >= 1:
        print 'Virus scan already performed, not running scan again'
        sys.exit(0)

    command = ['clamdscan', '-']
    print 'Clamscan command:', ' '.join(command), '<', target
    with open(target) as file_:
        scan_rc, scan_stdout, scan_stderr = executeOrRun("command", command, printing=False, stdIn=file_)
    commandVersion = "clamdscan -V"
    print 'Clamscan version command:', commandVersion
    version_rc, version_stdout, version_stderr = executeOrRun("command", commandVersion, printing=False)

    eventOutcome = "Pass"
    if scan_rc or version_rc:  # Either command returned non-0 RC
        if version_rc:
            print >>sys.stderr, 'Error determining version, aborting'
            print >>sys.stderr, 'Version RC:', version_rc
            print >>sys.stderr, 'Version Standard output:', version_stdout
            print >>sys.stderr, 'Version Standard error:', version_stderr
            sys.exit(2)
        else:
            eventOutcome = "Fail"

    clamscanResultShouldBe = "Infected files: 0"
    if eventOutcome == "Fail" or scan_stdout.find(clamscanResultShouldBe) == -1:
        eventOutcome = "Fail"
        print >>sys.stderr, 'Scan failed for file', fileUUID, " - ", os.path.basename(target)
        print >>sys.stderr, 'Clamscan RC:', scan_rc
        print >>sys.stderr, 'Clamscan Standard output:', scan_stdout
        print >>sys.stderr, 'Clamscan Standard error:', scan_stderr

    version, virusDefs, virusDefsDate = version_stdout.split("/")
    virusDefs = virusDefs + "/" + virusDefsDate
    eventDetailText = 'program="Clam AV"; version="' + version + '"; virusDefinitions="' + virusDefs + '"'

    print 'Event outcome:', eventOutcome
    if fileUUID != "None":
        insertIntoEvents(fileUUID=fileUUID, eventIdentifierUUID=taskUUID, eventType="virus check", eventDateTime=date, eventDetail=eventDetailText, eventOutcome=eventOutcome, eventOutcomeDetailNote="")
    if eventOutcome != "Pass":
        sys.exit(3)
