#!/usr/bin/env python2

from optparse import OptionParser

import django
django.setup()
# dashboard
from main.models import File

# archivematicaCommon
from databaseFunctions import insertIntoEvents


if __name__ == '__main__':
    """creates events for all files in the group"""
    parser = OptionParser()
    parser.add_option("-i",  "--groupUUID",          action="store", dest="groupUUID", default="")
    parser.add_option("-g",  "--groupType",          action="store", dest="groupType", default="")
    parser.add_option("-t",  "--eventType",        action="store", dest="eventType", default="")
    parser.add_option("-d",  "--eventDateTime",     action="store", dest="eventDateTime", default="")
    parser.add_option("-e",  "--eventDetail",       action="store", dest="eventDetail", default="")
    parser.add_option("-o",  "--eventOutcome",      action="store", dest="eventOutcome", default="")
    parser.add_option("-n",  "--eventOutcomeDetailNote",   action="store", dest="eventOutcomeDetailNote", default="")
    parser.add_option("-u",  "--eventIdentifierUUID",      action="store", dest="eventIdentifierUUID", default="")


    (opts, args) = parser.parse_args()
    kwargs = {
        "removedtime__isnull": True,
        opts.groupType: opts.groupUUID
    }
    file_uuids = File.objects.filter(**kwargs).values_list('uuid')
    for fileUUID, in file_uuids:
        insertIntoEvents(fileUUID=fileUUID, \
                     eventIdentifierUUID=opts.eventIdentifierUUID, \
                     eventType=opts.eventType, \
                     eventDateTime=opts.eventDateTime, \
                     eventDetail=opts.eventDetail, \
                     eventOutcome=opts.eventOutcome, \
                     eventOutcomeDetailNote=opts.eventOutcomeDetailNote)
