#!/usr/bin/env python2

import sys
import uuid
from optparse import OptionParser

import django
django.setup()
# dashboard
from main.models import File
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import addFileToTransfer
from fileOperations import addFileToSIP



if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.assignFileUUID")

    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-p",  "--filePath",          action="store", dest="filePath", default="")
    parser.add_option("-d",  "--date",              action="store", dest="date", default="")
    parser.add_option("-u",  "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    parser.add_option("-s",  "--sipDirectory", action="store", dest="sipDirectory", default="")
    parser.add_option("-S",  "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-T",  "--transferUUID", action="store", dest="transferUUID", default="")
    parser.add_option("-e",  "--use", action="store", dest="use", default="original")
    parser.add_option("--disable-update-filegrpuse", action="store_false", dest="update_use", default=True)


    (opts, args) = parser.parse_args()
    opts2 = vars(opts)
#    for key, value in opts2.iteritems():
#        print type(key), key, type(value), value
#        exec 'opts.' + key + ' = value.decode("utf-8")'
    fileUUID = opts.fileUUID
    if not fileUUID or fileUUID == "None":
        fileUUID = uuid.uuid4().__str__()
    else:
        print >>sys.stderr, "File already has UUID:", fileUUID
        if opts.update_use:
            File.objects.filter(uuid=fileUUID).update(filegrpuse=opts.use)
        exit(0) 


    if opts.sipUUID == "" and opts.transferUUID != "":
        filePathRelativeToSIP = opts.filePath.replace(opts.sipDirectory,"%transferDirectory%", 1)
        addFileToTransfer(filePathRelativeToSIP, fileUUID, opts.transferUUID, opts.eventIdentifierUUID, opts.date, use=opts.use)

    elif opts.sipUUID != "" and opts.transferUUID == "":
        filePathRelativeToSIP = opts.filePath.replace(opts.sipDirectory,"%SIPDirectory%", 1)
        addFileToSIP(filePathRelativeToSIP, fileUUID, opts.sipUUID, opts.eventIdentifierUUID, opts.date, use=opts.use)

    else:
        print >>sys.stderr, "SIP exclusive-or Transfer uuid must be defined"
        exit(2)
