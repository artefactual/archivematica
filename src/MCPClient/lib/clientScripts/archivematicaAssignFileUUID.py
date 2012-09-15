#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2012 Artefactual Systems Inc. <http://artefactual.com>
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
# @version svn: $Id$
import sys
import uuid
from optparse import OptionParser
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from fileOperations import addFileToTransfer
from fileOperations import addFileToSIP


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i",  "--fileUUID",          action="store", dest="fileUUID", default="")
    parser.add_option("-p",  "--filePath",          action="store", dest="filePath", default="")
    parser.add_option("-d",  "--date",              action="store", dest="date", default="")
    parser.add_option("-u",  "--eventIdentifierUUID", action="store", dest="eventIdentifierUUID", default="")
    parser.add_option("-s",  "--sipDirectory", action="store", dest="sipDirectory", default="")
    parser.add_option("-S",  "--sipUUID", action="store", dest="sipUUID", default="")
    parser.add_option("-T",  "--transferUUID", action="store", dest="transferUUID", default="")
    parser.add_option("-e",  "--use", action="store", dest="use", default="original")


    (opts, args) = parser.parse_args()
    opts2 = vars(opts)
#    for key, value in opts2.iteritems():
#        print type(key), key, type(value), value
#        exec 'opts.' + key + ' = value.decode("utf-8")'
    fileUUID = opts.fileUUID
    if not fileUUID or fileUUID == "None":
        fileUUID = uuid.uuid4().__str__()


    if opts.sipUUID == "" and opts.transferUUID != "":
        filePathRelativeToSIP = opts.filePath.replace(opts.sipDirectory,"%transferDirectory%", 1)
        addFileToTransfer(filePathRelativeToSIP, fileUUID, opts.transferUUID, opts.eventIdentifierUUID, opts.date, use=opts.use)

    elif opts.sipUUID != "" and opts.transferUUID == "":
        filePathRelativeToSIP = opts.filePath.replace(opts.sipDirectory,"%SIPDirectory%", 1)
        addFileToSIP(filePathRelativeToSIP, fileUUID, opts.sipUUID, opts.eventIdentifierUUID, opts.date, use=opts.use)

    else:
        print >>sys.stderr, "SIP exclusive-or Transfer uuid must be defined"
        exit(2)
