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


<<<<<<< 2c887e8c534aba024ae44c355a3a2388f9916ac1
def verify_bag(bag):
    verificationCommands = [
        ["/usr/share/bagit/bin/bag", "verifyvalid", bag],  # Validity
        ["/usr/share/bagit/bin/bag", "verifycomplete", bag],  # Completness
        ["/usr/share/bagit/bin/bag", "verifypayloadmanifests", bag],  # Checksums in manifests
    ]
    bagInfoPath = os.path.join(bag, "bag-info.txt")
    if os.path.isfile(bagInfoPath):
        for line in open(bagInfoPath, 'r'):
            if line.startswith("Payload-Oxum"):
                # Generate Payload-Oxum and check against Payload-Oxum in bag-info.txt.
                verificationCommands.append(
                    ["/usr/share/bagit/bin/bag", "checkpayloadoxum", bag]
                )
                break

    for item in os.listdir(bag):
        if item.startswith("tagmanifest-") and item.endswith(".txt"):
            # Verify the checksums in all tag manifests.
            verificationCommands.append(
                ["/usr/share/bagit/bin/bag", "verifytagmanifests", bag]
            )
            break

    exitCode = 0
    for command in verificationCommands:
        ret = executeOrRun("command", command)
        rc, _, _ = ret
        if rc != 0:
            print("Failed test: %s", command, file=sys.stderr)
            exitCode = 1
        else:
            print("Passed test: %s", command)
    return exitCode

if __name__ == '__main__':
    bag = sys.argv[1]
    sys.exit(verify_bag(bag))
=======
def verifyBAG(path):
    bag_info = os.path.join(path, BAG_INFO)
    verification_commands = [
        '{} verifyvalid {}'.format(BAG, path),              # Verifies the validity of a bag
        '{} verifycomplete {}'.format(BAG, path),           # Verifies the completeness of a bag
        '{} verifypayloadmanifests {}'.format(BAG, path),   # Verifies the checksums in all payload manifests
    ]

    if os.path.isfile(bag_info):
        for line in open(bag_info, 'r'):
            if line.startswith('Payload-Oxum'):
                verification_commands.append('{} checkpayloadoxum {}'.format(BAG, path)) # Generates Payload-Oxum and checks against Payload-Oxum in bag-info.txt
                break

    for item in os.listdir(path):
        if item.startswith('tagmanifest-') and item.endswith('.txt'):
            verification_commands.append('{} verifytagmanifests {}'.format(BAG, path)) # Verifies the checksums in all tag manifests
            break

    exit_code = 0
    for command in verification_commands:
        exit, stdout, stderr = executeOrRun('command', command, printing=PRINT_SUBPROCESS_OUTPUT)
        if exit != 0:
            print('Failed test:', command, file=sys.stderr)
            exit_code = 1
        else:
            print('Passed test:', command, file=sys.stderr)

    return exit_code


if __name__ == '__main__':
    sys.exit(verifyBAG(sys.argv[1]))
>>>>>>> Re-ingest: update transfer clientScripts
