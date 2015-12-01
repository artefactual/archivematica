#!/usr/bin/env python2

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
