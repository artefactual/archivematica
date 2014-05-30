#!/usr/bin/python -OO

# This file is part of Archivematica.
#
# Copyright 2010-2011 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
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
# @author Mike Cantelon <mike@artefactual.com>
import ConfigParser
import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import elasticSearchFunctions

exitCode = 0

if __name__ == '__main__':
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
