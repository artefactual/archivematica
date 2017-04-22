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
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
import archivematicaMCP
import cPickle
import gearman
import logging
import lxml.etree as etree
from socket import gethostname
import time

from linkTaskManagerChoice import choicesAvailableForUnits


LOGGER = logging.getLogger("archivematica.mcp.server.rpcserver")

def rpcError(code="", details=""):
    ret = etree.Element("Error")
    etree.SubElement(ret, "code").text = code.__str__()
    etree.SubElement(ret, "details").text = details.__str__()
    return ret


def getJobsAwaitingApproval():
    ret = etree.Element("choicesAvailableForUnits")
    for UUID, choice in choicesAvailableForUnits.items():
        ret.append(choice.xmlify())
    return etree.tostring(ret, pretty_print=True)


def approveJob(jobUUID, chain, user_id):
    LOGGER.debug("Approving: %s %s %s", jobUUID, chain, user_id)
    if jobUUID in choicesAvailableForUnits:
        choicesAvailableForUnits[jobUUID].proceedWithChoice(chain, user_id)
    return "approving: ", jobUUID, chain

def gearmanApproveJob(gearman_worker, gearman_job):
    try:
        data = cPickle.loads(gearman_job.data)
        jobUUID = data["jobUUID"]
        chain = data["chain"]
        user_id = str(data["uid"])
        return cPickle.dumps(approveJob(jobUUID, chain, user_id))
    # catch OS errors
    except Exception:
        LOGGER.exception('Error approving job')
        raise

def gearmanGetJobsAwaitingApproval(gearman_worker, gearman_job):
    try:
        return cPickle.dumps(getJobsAwaitingApproval())
    # catch OS errors
    except Exception:
        LOGGER.exception('Error getting jobs awaiting approval')
        raise


def startRPCServer():
    gm_worker = gearman.GearmanWorker([archivematicaMCP.config.get('MCPServer', 'GearmanServerWorker')])
    hostID = gethostname() + "_MCPServer"
    gm_worker.set_client_id(hostID)
    gm_worker.register_task("approveJob", gearmanApproveJob)
    gm_worker.register_task("getJobsAwaitingApproval", gearmanGetJobsAwaitingApproval)
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
