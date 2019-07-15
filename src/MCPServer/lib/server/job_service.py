from __future__ import absolute_import, unicode_literals

import logging

import grpc
from lxml import etree
from google.protobuf.empty_pb2 import Empty
from django.db import connection

from main.models import Job, Transfer

from linkTaskManagerChoice import choicesAvailableForUnits, choicesAvailableForUnitsLock
from package import create_package, get_approve_transfer_chain_id
from processing_config import get_processing_fields

from .protobuf_utils import datetime_to_timestamp
from .rpcgen import job_pb2_grpc
from .rpcgen.job_pb2 import (
    ApproveTransferResponse,
    CreatePackageResponse,
    GetProcessingConfigResponse,
    ListJobsAwaitingApprovalResponse,
    JobStatusResponse,
    SIPStatusesResponse,
    TransferStatusesResponse,
    UnitStatusResponse,
    WorkflowLink,
)


logger = logging.getLogger("archivematica.mcp.server")


# Theses queries can't be easily moved to the ORM :(
SIP_STATUS_SQL = """
SELECT SIPUUID,
MAX(createdTime) AS timestamp
FROM Jobs
WHERE unitType = "unitSIP"
AND SIPUUID IN (SELECT sipUUID FROM SIPs WHERE hidden = 0)
GROUP BY SIPUUID;"""
TRANSFER_STATUS_SQL = """
SELECT SIPUUID,
MAX(createdTime) AS timestamp
FROM Jobs
WHERE unitType = "unitTransfer"
AND SIPUUID IN (SELECT transferUUID FROM Transfers WHERE hidden = 0)
GROUP BY SIPUUID;"""


# TODO: shared data structures need to move to redis
def _pull_choices(job_id, lang, jobs_awaiting_for_approval):
    """Look up choices available in a job awaiting for approval.

    The choices (dict ``jobs_awaiting_for_approval``) must be provided so the
    caller can read it only once and use it many times, to minimize access to
    it as it in shared memory.

    The value returned is a dict ultimately used to hydrate a dropdown. The
    keys can be either IDs or indices depending on the underlying link manager.
    The value is the label that we want to show in the user interface, which
    is extracted from the instance of ``workflow.TranslationLabel`` hold by
    the link manager, given the ``lang`` of the user that made the request.
    """
    ret = {}
    choices = jobs_awaiting_for_approval[job_id].choices
    for item in choices:
        id_, label, rd = item
        ret[str(id_)] = label[lang]
    return ret


def get_job_status_responses(jobs, language, workflow):
    # TODO: shared data structures need to move to redis
    # This is a shared data structure, so make a copy to read.
    with choicesAvailableForUnitsLock:
        jobs_waiting_for_approval = choicesAvailableForUnits.copy()

    for job in jobs:
        try:
            link = workflow.get_link(job.microservicechainlink)
        except KeyError:
            workflow_link = None
        else:
            workflow_link = WorkflowLink(
                uuid=link.id,
                group_name=link.get_label("group", language),
                description=link.get_label("description", language),
            )
        try:
            choices = _pull_choices(job.jobuuid, language, jobs_waiting_for_approval)
        except (KeyError, AttributeError):
            choices = None

        job_status = JobStatusResponse(
            uuid=job.jobuuid,
            create_time=datetime_to_timestamp(job.createdtime),
            current_step=job.currentstep,
            workflow_link=workflow_link,
            choices=choices,
        )

        yield job_status


class JobServiceServicer(job_pb2_grpc.JobServiceServicer):
    def __init__(self, workflow):
        super(JobServiceServicer, self).__init__()
        self.workflow = workflow

    def CreatePackage(self, request, context):
        package = create_package(
            request.name,
            request.type or None,
            request.accession_id,
            request.access_system_id,
            request.path,
            request.metadata_set_id,
            request.user_id,
            self.workflow,
            auto_approve=request.auto_approve,
            processing_config=request.processing_config or None,
        )

        return CreatePackageResponse(uuid=package.pk)

    def ApproveJob(self, request, context):
        if request.job_uuid not in choicesAvailableForUnits:
            context.abort(grpc.StatusCode.NOT_FOUND, "Job not found")

        job_choice = choicesAvailableForUnits[request.job_uuid]
        job_choice.proceedWithChoice(request.chain_uuid, request.user_id)

        return Empty()

    def ApproveTransfer(self, request, context):
        job = Job.objects.filter(
            directory=request.db_transfer_path, currentstep=Job.STATUS_AWAITING_DECISION
        ).first()
        if not job:
            context.abort(grpc.StatusCode.NOT_FOUND, "Job not found")

        transfer_type = request.transfer_type or "standard"
        chain_id = get_approve_transfer_chain_id(transfer_type)

        try:
            choicesAvailableForUnits[job.pk].proceedWithChoice(
                chain_id, request.user_id
            )
        except KeyError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Choice not found")

        return ApproveTransferResponse(uuid=job.sipuuid)

    def ApprovePartialReingest(self, request, context):
        job = Job.objects.filter(
            sipuuid=request.uuid,
            microservicegroup="Reingest AIP",
            currentstep=Job.STATUS_AWAITING_DECISION,
        ).first()
        if not job:  # No job to be found.
            message = 'There is no "Reingest AIP" job awaiting a decision for SIP {}'.format(
                request.uuid
            )
            context.abort(grpc.StatusCode.NOT_FOUND, message)

        try:
            chain = self.workflow.get_chain(self.APPROVE_AIP_REINGEST_CHAIN_ID)
        except KeyError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Reingest choice chain not found")

        try:
            choicesAvailableForUnits[job.pk].proceedWithChoice(
                chain.id, request.user_id
            )
        except IndexError:
            context.abort(grpc.StatusCode.NOT_FOUND, "Available choice not found")

        return Empty()

    def ListJobsAwaitingApproval(self, request, context):
        choice_xml = etree.Element("choicesAvailableForUnits")

        with choicesAvailableForUnitsLock:
            for _, choice in choicesAvailableForUnits.items():
                choice_xml.append(choice.xmlify())

        return ListJobsAwaitingApprovalResponse(job_xml=[etree.tostring(choice_xml)])

    def ListSIPStatuses(self, request, context):
        with connection.cursor() as cursor:
            cursor.execute(SIP_STATUS_SQL)
            sips = cursor.fetchall()

        sip_statuses = []
        for sip_uuid, timestamp in sips:
            sip_jobs = Job.objects.filter(sipuuid=sip_uuid).order_by("-createdtime")
            job_responses = list(
                get_job_status_responses(sip_jobs, request.language, self.workflow)
            )
            sip_status = SIPStatusesResponse.SIPStatus(
                uuid=sip_uuid,
                # timestamp is already a UTC datetime
                update_time=datetime_to_timestamp(timestamp),
                jobs=job_responses,
            )

            transfer = Transfer.objects.filter(file__sip_id=sip_uuid).first()
            if transfer:
                sip_status.access_system_id = transfer.access_system_id
            if sip_jobs:
                sip_status.current_directory = sip_jobs[0].get_directory_name()

            sip_statuses.append(sip_status)

        return SIPStatusesResponse(sips=sip_statuses)

    def ListTransferStatuses(self, request, context):
        with connection.cursor() as cursor:
            cursor.execute(TRANSFER_STATUS_SQL)
            transfers = cursor.fetchall()

        transfer_statuses = []
        for transfer_uuid, timestamp in transfers:
            transfer_jobs = Job.objects.filter(sipuuid=transfer_uuid).order_by(
                "-createdtime"
            )
            job_responses = list(
                get_job_status_responses(transfer_jobs, request.language, self.workflow)
            )
            transfer_status = TransferStatusesResponse.TransferStatus(
                uuid=transfer_uuid,
                # timestamp is already a UTC datetime
                update_time=datetime_to_timestamp(timestamp),
                jobs=job_responses,
            )

            if transfer_jobs:
                transfer_status.current_directory = transfer_jobs[
                    0
                ].get_directory_name()

            transfer_statuses.append(transfer_status)

        return TransferStatusesResponse(transfers=transfer_statuses)

    def GetUnitStatus(self, request, context):
        job_queryset = Job.objects.filter(sipuuid=request.uuid)
        if not job_queryset.exists():
            context.abort(grpc.StatusCode.NOT_FOUND, "No jobs found for unit")

        current_directory = None
        job_statuses = []
        for job in job_queryset:
            if current_directory is None:
                current_directory = job.get_directory_name()

            try:
                link = self.workflow.get_link(job.microservicechainlink)
            except KeyError:
                continue

            link_description = link.get_label("description", request.language)
            link_group_name = link.get_label("group", request.language)

            job_status = JobStatusResponse(
                uuid=job.jobuuid,
                current_step=job.currentstep,
                create_time=datetime_to_timestamp(job.createdtime),
                workflow_link=WorkflowLink(
                    uuid=link.id,
                    description=link_description,
                    group_name=link_group_name,
                ),
            )
            job_statuses.append(job_status)

        return UnitStatusResponse(
            uuid=request.uuid, current_directory=current_directory, jobs=job_statuses
        )

    def GetProcessingConfig(self, request, context):
        fields = get_processing_fields(self.workflow)
        field_responses = [
            GetProcessingConfigResponse.ProcessingField(
                uuid=field_uuid,
                type=field.get("type", ""),
                name=field.get("name", ""),
                label=field.get("label", ""),
                ignored_choices=field.get("ignored_choices", []),
                find_duplicates=field.get("find_duplicates", False),
                yes_option_uuid=field.get("yes_option", ""),
                no_option_uuid=field.get("no_option", ""),
                purpose=field.get("purpose", ""),
                chain_uuid=field.get("chain", ""),
                options=field.get("options", {}),
            )
            for field_uuid, field in fields.items()
        ]

        return GetProcessingConfigResponse(fields=field_responses)


def add_servicer(server, workflow):
    servicer = JobServiceServicer(workflow)
    job_pb2_grpc.add_JobServiceServicer_to_server(servicer, server)
