#!/usr/bin/env python

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

import os
import shutil
import sys

from custom_handlers import get_script_logger

# FIXME run this SQL to use this script
#    update StandardTasksConfigs set `execute` = 'removeDirectories_v0.0', `arguments` = '"%SIPDirectory%%SIPName%-%SIPUUID%" "%SIPLogsDirectory%" "%SIPObjectsDirectory%" "%SIPDirectory%thumbnails/"' where pk = 'd12b6b59-1f1c-47c2-b1a3-2bf898740eae';
# And turn this into a migration at some point

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.removeDirectories")

    thumbnailDirectory = sys.argv[1:]
    dipDirectory = sys.argv[2]

    for directory in sys.argv[1:]:
        if os.path.isdir(directory):
            logger.info('Removing directory: %s', directory)
            shutil.rmtree(directory)
        else:
            logger.info('Directory does not exist: %s', directory)
