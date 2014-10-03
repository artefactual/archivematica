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
import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.backlogUpdatingTransferFileIndex")

    #"%SIPUUID%" "%SIPName%" "%SIPDirectory%"
    transferUUID = sys.argv[1]
    transferName = sys.argv[2]
    transferDirectory = sys.argv[3]
    print 'Processing ' + transferUUID + '...'
    found = elasticSearchFunctions.connect_and_change_transfer_file_status(transferUUID, 'backlog') 
    print 'Updated ' + str(found) + ' transfer file entries.'
