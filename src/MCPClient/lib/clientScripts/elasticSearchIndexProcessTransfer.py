#!/usr/bin/env python2

import ConfigParser
import sys

# elasticSearchFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions

exitCode = 0

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.elasticSearchIndexProcessTransfer")

    clientConfigFilePath = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(clientConfigFilePath)

    elasticsearchDisabled = False

    try:
        elasticsearchDisabled = config.getboolean('MCPClient', "disableElasticsearchIndexing")
    except:
        pass

    if elasticsearchDisabled is True:
        print 'Skipping indexing: indexing is currently disabled in ' + clientConfigFilePath + '.'

    else:
        pathToTransfer = sys.argv[1]
        transferUUID = sys.argv[2]

        exitCode = elasticSearchFunctions.connect_and_index_files(
            'transfers',
            'transferfile',
            transferUUID,
            pathToTransfer
        )

quit(exitCode)
