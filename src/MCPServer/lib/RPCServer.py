"""Archivematica MCPServer RPC.

We have plans to replace this server using gRPC.
"""

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

import cPickle
import logging
import lxml.etree as etree
from socket import gethostname
import time

from django.conf import settings as django_settings
import gearman

from databaseFunctions import auto_close_db
from linkTaskManagerChoice import choicesAvailableForUnits
from package import create_package, get_approve_transfer_chain_id
from processing_config import get_processing_fields
from main.models import Job, MicroServiceChainChoice


logger = logging.getLogger("archivematica.mcp.server.rpcserver")


class RPCServerError(Exception):
    """Base exception of RPCServer.

    This exception and its subclasses are meant to be raised by RPC handlers.
    """


class UnexpectedPayloadError(RPCServerError):
    """Missing parameters in payload."""


class NotFoundError(RPCServerError):
    """Generic NotFound exception."""


def capture_exceptions(raise_exc=True):
    """Worker handler decorator to capture and log handler exceptions.

    All the exceptions are logged. Tracebacks are included only when the
    exception is not an instance of ``RPCServerError``.

    If ``raise_exc`` is True, handler exceptions are raised. This is
    interpreted by the worker library as a failed job and the client will not
    receive additional information about the error other than its status.
    Set ``raise_exc`` to False when you want the client to receive a detailed
    error.
    """
    def decorator(func):
        def wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                is_handler_err = isinstance(err, RPCServerError)
                logger.error('Exception raised by handler %s: %s',
                             func.__name__, err, exc_info=not is_handler_err)

                if raise_exc:
                    raise  # So GearmanWorker knows that it failed.
                return {
                    "error": True,
                    "handler": func.__name__,
                    "message": str(err),
                }
        return wrap
    return decorator


def unpickle_payload(fn):
    """Worker handler decorator to unpickle the incoming payload.

    It prepends an argument before calling the decorated function.
    """
    def wrap(*args, **kwargs):
        gearman_job = args[1]
        payload = cPickle.loads(gearman_job.data)
        if not isinstance(payload, dict):
            raise UnexpectedPayloadError('Payload is not a dictionary')
        kwargs['payload'] = payload
        return fn(*args, **kwargs)
    return wrap


def pickle_result(fn):
    """Worker handler decorator to pickle the returned value."""
    def wrap(*args, **kwargs):
        return cPickle.dumps(fn(*args, **kwargs))
    return wrap


@auto_close_db
@pickle_result
@unpickle_payload
@capture_exceptions()
def job_approve_handler(*args, **kwargs):
    payload = kwargs['payload']
    job_id = payload["jobUUID"]
    chain = payload["chain"]
    user_id = str(payload["uid"])
    logger.debug("Approving: %s %s %s", job_id, chain, user_id)
    if job_id in choicesAvailableForUnits:
        choicesAvailableForUnits[job_id].proceedWithChoice(chain, user_id)
    return "approving: ", job_id, chain


@auto_close_db
@pickle_result
@capture_exceptions()
def job_awaiting_approval_handler(*args):
    ret = etree.Element('choicesAvailableForUnits')
    for uuid, choice in choicesAvailableForUnits.items():
        ret.append(choice.xmlify())
    return etree.tostring(ret, pretty_print=True)


@auto_close_db
@pickle_result
@unpickle_payload
@capture_exceptions()
def package_create_handler(*args, **kwargs):
    """Handle create package request."""
    payload = kwargs['payload']
    args = (
        payload.get('name'),
        payload.get('type'),
        payload.get('accession'),
        payload.get('access_system_id'),
        payload.get('path'),
        payload.get('metadata_set_id'),
    )
    kwargs = {
        'auto_approve': payload.get('auto_approve'),
        'wait_until_complete': payload.get('wait_until_complete'),
    }
    processing_config = payload.get('processing_config')
    if processing_config is not None:
        kwargs['processing_config'] = processing_config
    return create_package(*args, **kwargs).pk


@auto_close_db
@pickle_result
@unpickle_payload
@capture_exceptions(raise_exc=False)
def approve_transfer_by_path_handler(*args, **kwargs):
    payload = kwargs["payload"]
    db_transfer_path = payload.get("db_transfer_path")
    transfer_type = payload.get("transfer_type", "standard")
    user_id = payload.get("user_id")
    job = Job.objects.filter(
        directory=db_transfer_path,
        currentstep=Job.STATUS_AWAITING_DECISION
    ).first()
    if not job:
        raise NotFoundError("There is no job awaiting a decision.")
    chain_id = get_approve_transfer_chain_id(transfer_type)
    try:
        choicesAvailableForUnits[job.pk].proceedWithChoice(
            chain_id, user_id)
    except IndexError:
        raise NotFoundError("Could not find choice for unit")
    return job.sipuuid


@auto_close_db
@pickle_result
@unpickle_payload
@capture_exceptions(raise_exc=False)
def approve_partial_reingest_handler(*args, **kwargs):
    """
    TODO: this is just a temporary way of getting the API to do the
    equivalent of clicking "Approve AIP reingest" in the dashboard when faced
    with "Approve AIP reingest". This is non-dry given
    ``approve_transfer_by_path_handler`` above.
    """
    payload = kwargs["payload"]
    sip_uuid = payload.get("sip_uuid")
    user_id = payload.get("user_id")

    job = Job.objects.filter(
        sipuuid=sip_uuid,
        microservicegroup="Reingest AIP",
        currentstep=Job.STATUS_AWAITING_DECISION,
    ).first()
    if not job:  # No job to be found.
        raise NotFoundError(
            'There is no "Reingest AIP" job awaiting a'
            " decision for SIP {}".format(sip_uuid))
    chain = MicroServiceChainChoice.objects.filter(
        choiceavailableatlink__currenttask__description="Approve AIP reingest",
        chainavailable__description="Approve AIP reingest"
    ).first()
    not_found = NotFoundError(
        "Could not find choice for approve AIP reingest")
    if not chain:
        raise not_found
    try:
        choicesAvailableForUnits[job.pk].proceedWithChoice(
            chain.chainavailable.pk, user_id)
    except IndexError:
        raise not_found


@auto_close_db
@pickle_result
@capture_exceptions(raise_exc=False)
def get_processing_config_fields_handler(*args, **kwargs):
    return get_processing_fields()


def startRPCServer():
    gm_worker = gearman.GearmanWorker([django_settings.GEARMAN_SERVER])
    hostID = gethostname() + "_MCPServer"
    gm_worker.set_client_id(hostID)

    # The tasks registered in this worker should not block.
    gm_worker.register_task(
        "approveJob", job_approve_handler)
    gm_worker.register_task(
        "getJobsAwaitingApproval", job_awaiting_approval_handler)
    gm_worker.register_task(
        "packageCreate", package_create_handler)
    gm_worker.register_task(
        "approveTransferByPath", approve_transfer_by_path_handler)
    gm_worker.register_task(
        "approvePartialReingest", approve_partial_reingest_handler)
    gm_worker.register_task(
        "getProcessingConfigFields", get_processing_config_fields_handler)

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
