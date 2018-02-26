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

import cPickle
import logging

from django.conf import settings
import gearman


LOGGER = logging.getLogger('archivematica.dashboard.mcp.client')


class RPCError(Exception):
    pass


INFLIGHT_POLL_TIMEOUT = 5.0


class MCPClient:
    def __init__(self):
        self.server = settings.GEARMAN_SERVER

    def execute(self, uuid, choice, uid=None):
        gm_client = gearman.GearmanClient([self.server])
        data = {}
        data["jobUUID"] = uuid
        data["chain"] = choice
        if uid is not None:
            data["uid"] = uid
        gm_client.submit_job("approveJob", cPickle.dumps(data), None)
        gm_client.shutdown()
        return

    def list(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getJobsAwaitingApproval", "", None)
        if completed_job_request.state == gearman.JOB_COMPLETE:
            return cPickle.loads(completed_job_request.result)
        elif completed_job_request.state == gearman.JOB_FAILED:
            raise RPCError("getJobsAwaitingApproval failed (check MCPServer logs)")

    def notifications(self):
        gm_client = gearman.GearmanClient([self.server])
        completed_job_request = gm_client.submit_job("getNotifications", "", None)
        gm_client.shutdown()
        if completed_job_request.state == gearman.JOB_COMPLETE:
            return cPickle.loads(completed_job_request.result)
        elif completed_job_request.state == gearman.JOB_FAILED:
            raise RPCError("getNotifications failed (check MCPServer logs)")

    def create_package(self, name, type_, accession, path, metadata_set_id):
        gm_client = gearman.GearmanClient([self.server])
        data = cPickle.dumps({
            'name': name,
            'type': type_,
            'accession': accession,
            'path': path,
            'metadata_set_id': metadata_set_id,
        })
        response = gm_client.submit_job('packageCreate', data,
                                        background=False,
                                        wait_until_complete=True,
                                        poll_timeout=INFLIGHT_POLL_TIMEOUT)
        gm_client.shutdown()
        if response.state == gearman.JOB_COMPLETE:
            return cPickle.loads(response.result)  # Transfer ID (pickled)
        elif response.state == gearman.JOB_FAILED:
            raise RPCError('MCPServer returned an error (check the logs)')
