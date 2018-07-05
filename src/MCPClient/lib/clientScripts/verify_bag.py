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

import os
import sys

# archivematicaCommon
from executeOrRunSubProcess import executeOrRun

PRINT_SUBPROCESS_OUTPUT = True
BAG = '/usr/share/bagit/bin/bag'
BAG_INFO = 'bag-info.txt'


def verify_bag(job, bag):
    verification_commands = [
        ["/usr/share/bagit/bin/bag", "verifyvalid", bag],  # Validity
        ["/usr/share/bagit/bin/bag", "verifycomplete", bag],  # Completness
        ["/usr/share/bagit/bin/bag", "verifypayloadmanifests", bag],  # Checksums in manifests
    ]
    bag_info = os.path.join(bag, "bag-info.txt")
    if os.path.isfile(bag_info):
        for line in open(bag_info, 'r'):
            if line.startswith("Payload-Oxum"):
                # Generate Payload-Oxum and check against Payload-Oxum in bag-info.txt.
                verification_commands.append(
                    ["/usr/share/bagit/bin/bag", "checkpayloadoxum", bag]
                )
                break

    for item in os.listdir(bag):
        if item.startswith("tagmanifest-") and item.endswith(".txt"):
            # Verify the checksums in all tag manifests.
            verification_commands.append(
                ["/usr/share/bagit/bin/bag", "verifytagmanifests", bag]
            )
            break

    exit_code = 0
    for command in verification_commands:
        ret = executeOrRun("command", command, capture_output=True)
        rc, stdout, stderr = ret
        job.write_output(stdout)
        job.write_error(stderr)
        if rc != 0:
            job.pyprint("Failed test: %s", command, file=sys.stderr)
            exit_code = 1
        else:
            job.pyprint("Passed test: %s", command)
    return exit_code


def call(jobs):
    for job in jobs:
        with job.JobContext():
            bag = job.args[1]
            job.set_status(verify_bag(job, bag))
