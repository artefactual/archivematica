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

from __future__ import print_function

import os
import sys

# archivematicaCommon
from custom_handlers import get_script_logger
from executeOrRunSubProcess import executeOrRun

logger = get_script_logger('archivematica.mcp.client.verifyBAG')

PRINT_SUBPROCESS_OUTPUT = True
BAG = '/usr/share/bagit/bin/bag'
BAG_INFO = 'bag-info.txt'


def verify_bag(path):
    bag_info = os.path.join(path, BAG_INFO)
    verification_commands = [
        '{} verifyvalid {}'.format(BAG, path),              # Verifies the validity of a bag
        '{} verifycomplete {}'.format(BAG, path),           # Verifies the completeness of a bag
        '{} verifypayloadmanifests {}'.format(BAG, path),   # Verifies the checksums in all payload manifests
    ]

    if os.path.isfile(bag_info):
        for line in open(bag_info, 'r'):
            if line.startswith("Payload-Oxum"):
                verification_commands.append('{} checkpayloadoxum {}'.format(BAG, path)) # Generates Payload-Oxum and checks against Payload-Oxum in bag-info.txt
                break

    for item in os.listdir(path):
        if item.startswith("tagmanifest-") and item.endswith(".txt"):
            verification_commands.append('{} verifytagmanifests {}'.format(BAG, path)) # Verifies the checksums in all tag manifests
            break

    exit_code = 0
    for command in verification_commands:
        exit_, stdout, stderr = executeOrRun('command', command, printing=PRINT_SUBPROCESS_OUTPUT)
        if exit_ != 0:
            print('Failed test:', command, file=sys.stderr)
            exit_code = 1
        else:
            print('Passed test:', command, file=sys.stderr)

    return exit_code


if __name__ == '__main__':
    sys.exit(verify_bag(sys.argv[1]))
