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
from glob import glob
import sys

# archivematicaCommon
from custom_handlers import get_script_logger
import elasticSearchFunctions
from identifier_functions import extract_identifiers_from_mods

exitCode = 0


def list_mods(sip_path):
    return glob('{}/objects/submissionDocumentation/mods/*.xml'.format(sip_path))

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.elasticSearchIndexProcessAIP")

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
        pathToAIP = sys.argv[1]
        uuid = sys.argv[2]
        sipName = sys.argv[3]

        # Even though we treat MODS identifiers as SIP-level, we need to index them here
        # because the archival storage tab actually searches on the aips/aipfile index.
        mods_paths = list_mods(pathToAIP)
        identifiers = []
        for mods in mods_paths:
            identifiers.extend(extract_identifiers_from_mods(mods))

        exitCode = elasticSearchFunctions.connect_and_index_files(
            'aips',
            'aipfile',
            uuid,
            pathToAIP,
            sipName=sipName,
            identifiers=identifiers
        )

quit(exitCode)
