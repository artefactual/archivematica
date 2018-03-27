"""Archivematica MCPServer RPC."""

# This file is part of Archivematica.
#
# Copyright 2010-2018 Artefactual Systems Inc. <http://artefactual.com>
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

import logging
import lxml.etree as etree
from socket import gethostname
import time

from django.conf import settings as django_settings
import gearman

from linkTaskManagerChoice import choicesAvailableForUnits
from package import create_package
from worker_util import log_exceptions, unpickle_payload, pickle_result


LOGGER = logging.getLogger("archivematica.mcp.server.rpcserver")


@pickle_result
@unpickle_payload
@log_exceptions(LOGGER)
def job_approve_handler(*args, **kwargs):
    payload = kwargs['payload']
    job_id = payload["jobUUID"]
    chain = payload["chain"]
    user_id = str(payload["uid"])
    LOGGER.debug("Approving: %s %s %s", job_id, chain, user_id)
    if job_id in choicesAvailableForUnits:
        choicesAvailableForUnits[job_id].proceedWithChoice(chain, user_id)
    return "approving: ", job_id, chain


@pickle_result
@log_exceptions(LOGGER)
def job_awaiting_approval_handler(*args):
    ret = etree.Element('choicesAvailableForUnits')
    for uuid, choice in choicesAvailableForUnits.items():
        ret.append(choice.xmlify())
    return etree.tostring(ret, pretty_print=True)


@pickle_result
@unpickle_payload
@log_exceptions(LOGGER)
def package_create_handler(*args, **kwargs):
    """Handle create package request."""
    payload = kwargs['payload']
    create_package_args = (
        payload.get('name'),
        payload.get('type'),
        payload.get('accession'),
        payload.get('path'),
        payload.get('metadata_set_id'),
        payload.get('auto_approve', True),
    )
    return create_package(*create_package_args).pk


def startRPCServer():
    gm_worker = gearman.GearmanWorker([django_settings.GEARMAN_SERVER])
    hostID = gethostname() + "_MCPServer"
    gm_worker.set_client_id(hostID)

    # The tasks registered in this worker should not block.
    gm_worker.register_task("approveJob", job_approve_handler)
    gm_worker.register_task("getJobsAwaitingApproval", job_awaiting_approval_handler)
    gm_worker.register_task("packageCreate", package_create_handler)

    failMaxSleep = 30
    failSleep = 1
    failSleepIncrementor = 2
    while True:
        try:
            gm_worker.work()
        except gearman.errors.ServerUnavailable:
            time.sleep(failSleep)
            if failSleep < failMaxSleep:
                failSleep += failSleepIncrementor
