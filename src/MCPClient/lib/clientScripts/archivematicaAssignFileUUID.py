#!/usr/bin/env python2

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
import os
import sys
import uuid
from optparse import OptionParser

import django
django.setup()
# dashboard
from main.models import File
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import addFileToTransfer, addFileToSIP, rename2unicode


def is_transfer(opts):
    return opts.sipUUID == "" and opts.transferUUID != ""


def is_ingest(opts):
    return opts.sipUUID != "" and opts.transferUUID == ""


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
    fileUUID = opts.fileUUID
    if not fileUUID or fileUUID == "None":
        fileUUID = uuid.uuid4().__str__()
    else:
        print >>sys.stderr, "File already has UUID:", fileUUID
        if opts.update_use:
            File.objects.filter(uuid=fileUUID).update(filegrpuse=opts.use)
        exit(0)

    if is_transfer(opts):
        bytestringFilePath = opts.filePath
        unicodeFilePath = rename2unicode(opts.filePath)
        unicodeFilePathRelativeToSIP = unicodeFilePath.replace(
            opts.sipDirectory, "%transferDirectory%", 1)
        bytestringFilePathRelativeToSIP = bytestringFilePath.replace(
            opts.sipDirectory, "%transferDirectory%", 1)
        addFileToTransfer(
            bytestringFilePathRelativeToSIP, fileUUID, opts.transferUUID,
            opts.eventIdentifierUUID, opts.date, use=opts.use,
            unicodeFilePathRelativeToSIP=unicodeFilePathRelativeToSIP)
    elif is_ingest(opts):
        filePathRelativeToSIP = opts.filePath.replace(
            opts.sipDirectory, "%SIPDirectory%", 1)
        addFileToSIP(
            filePathRelativeToSIP, fileUUID, opts.sipUUID,
            opts.eventIdentifierUUID, opts.date, use=opts.use)
    else:
        print >>sys.stderr, "SIP exclusive-or Transfer uuid must be defined"
        exit(2)
