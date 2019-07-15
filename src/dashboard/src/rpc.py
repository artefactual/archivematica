from __future__ import absolute_import, unicode_literals

import functools

import gevent.monkey
import grpc
import grpc.experimental.gevent
from google.protobuf.empty_pb2 import Empty
from django.utils.translation import get_language

from rpcgen.job_pb2_grpc import JobServiceStub
from rpcgen.job_pb2 import (
    ApproveJobRequest,
    ApproveTransferRequest,
    ApprovePartialReingestRequest,
    CreatePackageRequest,
    SIPStatusesRequest,
    TransferStatusesRequest,
    UnitStatusRequest,
)


# Socket is arbitrary here; we just need to know if any monkeypatching has been done,
# so that we can also patch gRPC.
if gevent.monkey.is_module_patched("socket"):
    grpc.experimental.gevent.init_gevent()


RPC_TIMEOUT = 5.0


class RPCError(OSError):
    """
    A generic RPC error.
    """


class TimeoutError(RPCError):
    """
    The RPC call timed out.
    """


def wrap_grpc_errors(func):
    """
    Wrapper to provide slightly friendlier error handling for RPC calls.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)
        except grpc.RpcError as rpc_error:
            if rpc_error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise TimeoutError(
                    "gRPC call timed out: {}".format(rpc_error.details())
                )
            # TODO: connect error
            else:
                raise RPCError(
                    "gRPC error {}: {}".format(
                        rpc_error.code().name, rpc_error.details()
                    )
                )

    return wrapper


def _get_channel():
    # TODO: connection persistence
    # TODO: server name setting
    return grpc.insecure_channel("archivematica-mcp-server:50051")


def _get_job_service_stub():
    channel = _get_channel()
    stub = JobServiceStub(channel)

    return stub


@wrap_grpc_errors
def create_package(
    name,
    package_type,
    accession_id,
    access_system_id,
    path,
    metadata_set_id,
    user_id,
    auto_approve=True,
    processing_config=None,
):
    stub = _get_job_service_stub()
    request = CreatePackageRequest(
        name=name,
        type=package_type,
        accession_id=accession_id,
        access_system_id=access_system_id,
        path=path,
        metadata_set_id=metadata_set_id,
        user_id=user_id,
        auto_approve=auto_approve,
        processing_config=processing_config,
    )

    return stub.CreatePackage(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def get_sip_statuses():
    stub = _get_job_service_stub()
    language = get_language()
    request = SIPStatusesRequest(language=language)

    return stub.ListSIPStatuses(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def get_transfer_statuses():
    stub = _get_job_service_stub()
    language = get_language()
    request = TransferStatusesRequest(language=language)

    return stub.ListTransferStatuses(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def get_unit_status(uuid):
    stub = _get_job_service_stub()
    language = get_language()
    request = UnitStatusRequest(uuid=uuid, language=language)

    return stub.GetUnitStatus(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def approve_job(job_uuid, chain_uuid, user_id):
    stub = _get_job_service_stub()
    request = ApproveJobRequest(
        job_uuid=job_uuid, chain_uuid=chain_uuid, user_id=user_id
    )

    return stub.ApproveJob(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def approve_transfer(transfer_type, db_transfer_path, user_id):
    stub = _get_job_service_stub()
    request = ApproveTransferRequest(
        transfer_type=transfer_type, db_transfer_path=db_transfer_path, user_id=user_id
    )

    return stub.ApproveTransfer(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def approve_partial_reingest(sip_uuid, user_id):
    stub = _get_job_service_stub()
    request = ApprovePartialReingestRequest(uuid=sip_uuid, user_id=user_id)

    return stub.ApprovePartialReingest(request, timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def list_jobs_awaiting_approval():
    stub = _get_job_service_stub()

    return stub.ListJobsAwaitingApproval(Empty(), timeout=RPC_TIMEOUT)


@wrap_grpc_errors
def get_processing_config_fields():
    stub = _get_job_service_stub()

    return stub.GetProcessingConfig(Empty(), timeout=RPC_TIMEOUT)
