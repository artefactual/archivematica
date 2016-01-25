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

logger = get_script_logger("archivematica.mcp.client.verifyBAG")

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
