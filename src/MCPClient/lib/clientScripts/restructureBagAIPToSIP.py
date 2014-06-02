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
import shutil

# archivematicaCommon
from custom_handlers import get_script_logger
import archivematicaFunctions

def _move_file(src, dst, exit_on_error=True):
    print 'Moving', src, 'to', dst
    try:
        shutil.move(src, dst)
    except IOError:
        print 'Could not move', src
        if exit_on_error:
            raise

if __name__ == '__main__':
    logger = get_script_logger("archivematica.mcp.client.restructureBagAIPToSIP")

    sip_path = sys.argv[1]

    # Move everything out of data directory
    for item in os.listdir(os.path.join(sip_path, 'data')):
        src = os.path.join(sip_path, 'data', item)
        dst = os.path.join(sip_path, item)
        _move_file(src, dst)

    os.rmdir(os.path.join(sip_path, 'data'))

    # Move metadata and logs out of objects if they exist
    src = os.path.join(sip_path, 'objects', 'metadata')
    dst = os.path.join(sip_path, 'metadata')
    _move_file(src, dst, exit_on_error=False)

    src = os.path.join(sip_path, 'objects', 'logs')
    dst = os.path.join(sip_path, 'logs')
    _move_file(src, dst, exit_on_error=False)

    # Move anything unexpected to submission documentation
    # Leave objects, metadata, etc
    # Original METS ends up in submissionDocumentation
    os.makedirs(os.path.join(sip_path, 'metadata', 'submissionDocumentation'))
    for item in os.listdir(sip_path):
        # Leave SIP structure
        if item in archivematicaFunctions.OPTIONAL_FILES + archivematicaFunctions.REQUIRED_DIRECTORIES:
            continue
        src = os.path.join(sip_path, item)
        dst = os.path.join(sip_path, 'metadata', 'submissionDocumentation', item)
        _move_file(src, dst)

    archivematicaFunctions.create_structured_directory(sip_path, manual_normalization=True, printing=True)
