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

from django.conf import settings
import gearman

from main.models import Job


class RPCError(Exception):
    pass


class NoJobFoundError(Exception):
    def __init__(self, *args, **kwargs):
        try:
            message = args[0]
        except IndexError:
            message = "No job was found"
        super(NoJobFoundError, self).__init__(message)


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

    def execute_unit(self, unit_id, choice, mscl_id=None, uid=None):
        """Execute the jobs awaiting for approval associated to a given unit.

        Use ``mscl_id`` to pass the ID of the chain link to restrict the
        execution to a single microservice.
        """
        kwargs = {
            'currentstep': Job.STATUS_AWAITING_DECISION,
            'sipuuid': unit_id,
        }
        if mscl_id is not None:
            kwargs['microservicechainlink_id'] = mscl_id
        jobs = Job.objects.filter(**kwargs)
        if len(jobs) < 1:
            raise NoJobFoundError()
        for item in jobs:
            self.execute(item.pk, choice, uid)

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
