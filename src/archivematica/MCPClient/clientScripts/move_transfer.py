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
"""Move a transfer and keep its database location synchronized.

The normal workflow calls this after content exists in a transfer directory, so
missing source paths should remain errors. API-created transfers add an earlier
retrieval task that may fail before anything is copied into ``%SIPDirectory%``.
The retrieval failure cleanup still follows the usual failed-transfer links, but
there is then no source directory to move into ``failed/``. The optional missing
source flag lets that specific cleanup path be a no-op while preserving strict
behavior for existing move-transfer callers.
"""

import os
from collections.abc import Sequence

import django

django.setup()
from archivematica.archivematicaCommon.fileOperations import rename
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client import transactions
from archivematica.MCPClient.client.job import Job


def updateDB(dst: str, transferUUID: str) -> None:
    """Store the shared-directory form of a transfer destination."""
    Transfer.objects.filter(uuid=transferUUID).update(currentlocation=dst)


def moveSIP(
    job: Job,
    src: str,
    dst: str,
    transferUUID: str,
    sharedDirectoryPath: str,
    allow_missing_source: bool = False,
) -> int:
    """Move a transfer, optionally treating an absent retrieval source as done."""
    # os.rename(src, dst)
    if src.endswith("/"):
        src = src[:-1]

    if allow_missing_source and not os.path.exists(src):
        # Retrieval failure cleanup has nothing to relocate when copy never began.
        job.pyprint("Transfer path does not exist; nothing to move:", src)
        return 0

    dest = dst.replace(sharedDirectoryPath, "%sharedPath%", 1)
    if dest.endswith("/"):
        dest = os.path.join(dest, os.path.basename(src))
    if dest.endswith("/."):
        dest = os.path.join(dest[:-1], os.path.basename(src))

    if os.path.isdir(src):
        dest += "/"
    updateDB(dest, transferUUID)

    return rename(src, dst, printfn=job.pyprint, should_exit=False)


def call(jobs: Sequence[Job]) -> None:
    """Run move tasks using arguments emitted by workflow links."""
    with transactions.atomic():
        for job in jobs:
            with job.JobContext():
                src = job.args[1]
                dst = job.args[2]
                transferUUID = job.args[3]
                sharedDirectoryPath = job.args[4]
                allow_missing_source = "--allow-missing-source" in job.args[5:]
                job.set_status(
                    moveSIP(
                        job,
                        src,
                        dst,
                        transferUUID,
                        sharedDirectoryPath,
                        allow_missing_source=allow_missing_source,
                    )
                )
