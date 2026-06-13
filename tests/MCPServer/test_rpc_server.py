import threading
import uuid
from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import rpc_server
from archivematica.MCPServer.server.jobs.chain import get_job_class_for_link

TASK_PRODUCING_LINK_ID = "002716a1-ae29-4f36-98ab-0d97192669c4"


@pytest.mark.django_db
def test_approve_partial_reingest_handler(wf):
    sip = models.SIP.objects.create(uuid=str(uuid.uuid4()))
    models.Job.objects.create(
        sipuuid=sip.pk,
        microservicegroup="Reingest AIP",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    server._approve_partial_reingest_handler(None, wf, {"sip_uuid": sip.pk})

    package_queue.decide.assert_called_once()


@pytest.mark.django_db
def test_units_statuses_handler_sets_produces_tasks_from_job_class(wf):
    task_producing_link = wf.get_link(TASK_PRODUCING_LINK_ID)
    assert get_job_class_for_link(task_producing_link).produces_tasks is True

    sip = models.SIP.objects.create(uuid=str(uuid.uuid4()))
    models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitSIP",
        microservicegroup="Test group",
        microservicechainlink=task_producing_link.id,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_EXECUTING_COMMANDS,
    )

    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_statuses_handler(None, None, {"type": "SIP", "lang": "en"})

    assert len(response) == 1
    assert len(response[0]["jobs"]) == 1
    assert response[0]["jobs"][0]["produces_tasks"] is True


@pytest.mark.django_db
def test_units_statuses_handler_keeps_only_retrieval_jobs_without_workflow_links(wf):
    transfer = models.Transfer.objects.create(uuid=str(uuid.uuid4()))
    retrieval_job = models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Transfer retrieval",
        jobtype="Retrieve contents from transfer source",
        microservicechainlink=None,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_UNKNOWN,
    )
    models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Orphaned workflow group",
        jobtype="Orphaned workflow job",
        microservicechainlink=None,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_UNKNOWN,
    )

    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_statuses_handler(
        None, None, {"type": "Transfer", "lang": "en"}
    )

    assert len(response) == 1
    assert len(response[0]["jobs"]) == 1
    job = response[0]["jobs"][0]
    assert job["uuid"] == str(retrieval_job.jobuuid)
    assert job["link_id"] is None
    assert job["currentstep"] == models.Job.STATUS_UNKNOWN
    assert job["microservicegroup"] == "Transfer retrieval"
    assert job["type"] == "Retrieve contents from transfer source"
    assert job["produces_tasks"] is False


@pytest.mark.django_db
def test_units_statuses_handler_shows_completed_retrieval_as_executing(wf):
    """Present active transfers as processing during the workflow handoff.

    This simulates retrieval having completed while the first workflow job has
    not been persisted yet. That can happen while the job is waiting in
    PackageQueue for a CONCURRENT_PACKAGES slot.
    """
    transfer = models.Transfer.objects.create(
        uuid=str(uuid.uuid4()), status=models.PACKAGE_STATUS_PROCESSING
    )
    retrieval_job = models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Transfer retrieval",
        jobtype="Retrieve contents from transfer source",
        microservicechainlink=None,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )

    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_statuses_handler(
        None, None, {"type": "Transfer", "lang": "en"}
    )

    assert len(response) == 1
    assert response[0]["active"] is True
    assert response[0]["jobs"][0]["uuid"] == str(retrieval_job.jobuuid)
    assert response[0]["jobs"][0]["currentstep"] == (
        models.Job.STATUS_EXECUTING_COMMANDS
    )

    retrieval_job.refresh_from_db()
    # The workaround is response-only; job history remains truthful.
    assert retrieval_job.currentstep == models.Job.STATUS_COMPLETED_SUCCESSFULLY


@pytest.mark.django_db
def test_units_statuses_handler_keeps_retrieval_done_after_workflow_starts(wf):
    """Stop the presentation override once a workflow job is visible."""
    created_time = timezone.now()
    transfer = models.Transfer.objects.create(
        uuid=str(uuid.uuid4()), status=models.PACKAGE_STATUS_PROCESSING
    )
    retrieval_job = models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Transfer retrieval",
        jobtype="Retrieve contents from transfer source",
        microservicechainlink=None,
        createdtime=created_time,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=created_time + timedelta(seconds=1),
        currentstep=models.Job.STATUS_EXECUTING_COMMANDS,
    )

    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_statuses_handler(
        None, None, {"type": "Transfer", "lang": "en"}
    )

    jobs = {job["uuid"]: job for job in response[0]["jobs"]}
    assert jobs[str(retrieval_job.jobuuid)]["currentstep"] == (
        models.Job.STATUS_COMPLETED_SUCCESSFULLY
    )


@pytest.mark.django_db
def test_unit_status_handler_keeps_only_retrieval_jobs_without_workflow_links(wf):
    transfer = models.Transfer.objects.create(uuid=str(uuid.uuid4()))
    retrieval_job = models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Transfer retrieval",
        jobtype="Retrieve contents from transfer source",
        microservicechainlink=None,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_UNKNOWN,
    )
    models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        microservicegroup="Orphaned workflow group",
        jobtype="Orphaned workflow job",
        microservicechainlink=None,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_UNKNOWN,
    )

    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._unit_status_handler(
        None, None, {"id": str(transfer.pk), "lang": "en"}
    )

    assert response["jobs"] == [
        {
            "id": retrieval_job.jobuuid,
            "description": "Retrieve contents from transfer source",
            "status": models.Job.STATUS_UNKNOWN,
            "group": "Transfer retrieval",
        }
    ]


@pytest.mark.django_db
def test_units_statuses_handler_returns_transfers(wf):
    transfer_uuid = str(uuid.uuid4())
    transfer = models.Transfer.objects.create(uuid=transfer_uuid)
    models.Job.objects.create(
        sipuuid=transfer.pk,
        unittype="unitTransfer",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert len(result) == 1
    assert result[0]["uuid"] == transfer_uuid


@pytest.mark.django_db
def test_units_statuses_handler_returns_sips(wf):
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(uuid=sip_uuid)
    models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitSIP",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(None, wf, {"type": "SIP", "lang": "en"})

    assert len(result) == 1
    assert result[0]["uuid"] == sip_uuid


@pytest.mark.django_db
def test_units_statuses_handler_excludes_hidden_transfers(wf):
    visible_transfer_uuid = str(uuid.uuid4())
    hidden_transfer_uuid = str(uuid.uuid4())
    visible_transfer = models.Transfer.objects.create(
        uuid=visible_transfer_uuid, hidden=False
    )
    hidden_transfer = models.Transfer.objects.create(
        uuid=hidden_transfer_uuid, hidden=True
    )
    models.Job.objects.create(
        sipuuid=visible_transfer.pk,
        unittype="unitTransfer",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    models.Job.objects.create(
        sipuuid=hidden_transfer.pk,
        unittype="unitTransfer",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert len(result) == 1
    assert result[0]["uuid"] == visible_transfer_uuid


@pytest.mark.django_db
def test_units_statuses_handler_excludes_hidden_sips(wf):
    visible_sip_uuid = str(uuid.uuid4())
    hidden_sip_uuid = str(uuid.uuid4())
    visible_sip = models.SIP.objects.create(uuid=visible_sip_uuid, hidden=False)
    hidden_sip = models.SIP.objects.create(uuid=hidden_sip_uuid, hidden=True)
    models.Job.objects.create(
        sipuuid=visible_sip.pk,
        unittype="unitSIP",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    models.Job.objects.create(
        sipuuid=hidden_sip.pk,
        unittype="unitSIP",
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink="7d728c39-395f-4892-8193-92f086c0546f",
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(None, wf, {"type": "SIP", "lang": "en"})

    assert len(result) == 1
    assert result[0]["uuid"] == visible_sip_uuid


@pytest.mark.django_db
def test_units_statuses_handler_raises_error_when_type_missing(wf):
    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)

    with pytest.raises(
        rpc_server.UnexpectedPayloadError, match="Missing parameter: 'type'"
    ):
        server._units_statuses_handler(None, wf, {"lang": "en"})


@pytest.mark.django_db
def test_units_statuses_handler_raises_error_when_lang_missing(wf):
    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)

    with pytest.raises(
        rpc_server.UnexpectedPayloadError, match="Missing parameter: 'lang'"
    ):
        server._units_statuses_handler(None, wf, {"type": "SIP"})
