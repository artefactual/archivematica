#!/usr/bin/env python2

import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.removeAIPFilesFromIndex")

    AIPUUID = sys.argv[1]
    print 'Removing indexed files for AIP ' + AIPUUID + '...'
    elasticSearchFunctions.connect_and_delete_aip_files(AIPUUID)
    print 'Done.'
