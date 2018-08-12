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

from main.models import Job


LOGGER = logging.getLogger('archivematica.dashboard.mcp.client')


class RPCGearmanClientError(Exception):
    """Base exception."""


class RPCError(RPCGearmanClientError):
    """Unexpected error."""


class RPCServerError(RPCGearmanClientError):
    """Server application errors.

    When the worker processes the job successfully but the response includes
    an error.
    """
    GENERIC_ERROR_MSG = "The server failed to process the request"

    def __init__(self, payload=None):
        super(RPCServerError, self).__init__(self._process_error(payload))

    def _process_error(self, payload):
        """Extracts the error message from the payload."""
        if payload is None or not isinstance(payload, dict):
            return self.GENERIC_ERROR_MSG
        message = payload.get("message", "Unknown error message")
        handler = payload.get("function")
        if handler:
            message += " [handler=%s]" % (handler,)
        return message


class TimeoutError(RPCGearmanClientError):
    """Deadline exceeded.

    >> response = client.submit_job(
           "doSomething", cPickle.dumps(data),
           background=False, wait_until_complete=True,
           poll_timeout=INFLIGHT_POLL_TIMEOUT)
       if response.state == gearman.JOB_CREATED:
           raise TimeoutError()

    At this point we give up and raise this exception.
    """
    def __init__(self, timeout=None):
        message = "Deadline exceeded"
        if timeout is not None:
            message = "{}: {}".format(message, timeout)
        super(TimeoutError, self).__init__(message)


class NoJobFoundError(RPCGearmanClientError):
    def __init__(self, message=None):
        if message is None:
            message = "No job was found"
        super(NoJobFoundError, self).__init__(message)


INFLIGHT_POLL_TIMEOUT = 5.0


class MCPClient(object):
    """MCPServer client (RPC via Gearman)."""

    def __init__(self):
        self.server = settings.GEARMAN_SERVER

    def _rpc_sync_call(self, ability, data, timeout=INFLIGHT_POLL_TIMEOUT):
        """Invoke remote method synchronously and with a deadline.

        When successful, it returns the payload of the response. Otherwise, it
        raises an exception. ``TimeoutError`` when the deadline was exceeded,
        ``RPCError`` when the worker failed abruptly, ``RPCServerError`` when
        the worker returned an error.
        """
        client = gearman.GearmanClient([self.server])
        response = client.submit_job(
            ability, cPickle.dumps(data),
            background=False, wait_until_complete=True,
            poll_timeout=timeout)
        client.shutdown()
        if response.state == gearman.JOB_CREATED:
            raise TimeoutError(timeout)
        elif response.state != gearman.JOB_COMPLETE:
            raise RPCError("%s failed (check the logs)".format(ability))
        payload = cPickle.loads(response.result)
        if isinstance(payload, dict) and payload.get("error", False):
            raise RPCServerError(payload)
        return payload

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
            "currentstep": Job.STATUS_AWAITING_DECISION,
            "sipuuid": unit_id,
        }
        if mscl_id is not None:
            kwargs["microservicechainlink_id"] = mscl_id
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

    def create_package(self, name, type_, accession, access_system_id, path,
                       metadata_set_id, auto_approve=True,
                       wait_until_complete=False, processing_config=None):
        data = {
            "name": name,
            "type": type_,
            "accession": accession,
            "access_system_id": access_system_id,
            "path": path,
            "metadata_set_id": metadata_set_id,
            "auto_approve": auto_approve,
            "wait_until_complete": wait_until_complete,
        }
        if processing_config is not None:
            data["processing_config"] = processing_config
        return self._rpc_sync_call("packageCreate", data)

    def approve_transfer_by_path(self, db_transfer_path,
                                 transfer_type, user_id):
        """Approve a transfer given its path and transfer type."""
        data = {
            "db_transfer_path": db_transfer_path,
            "transfer_type": transfer_type,
            "user_id": user_id,
        }
        return self._rpc_sync_call("approveTransferByPath", data)

    def approve_partial_reingest(self, sip_uuid, user_id):
        """Approve a partial reingest awaiting for approval."""
        data = {"sip_uuid": sip_uuid, "user_id": user_id}
        return self._rpc_sync_call("approvePartialReingest", data)
