import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone
from unittest import mock

import pytest
from django.utils import timezone

from archivematica.dashboard.main import models
from archivematica.MCPServer.server import rpc_server
from archivematica.MCPServer.server.jobs.chain import get_job_class_for_link
from archivematica.MCPServer.server.queues import PackageQueue

TASK_PRODUCING_LINK_ID = "002716a1-ae29-4f36-98ab-0d97192669c4"


def test_datetime_to_unix_timestamp_preserves_utc_microseconds():
    value = datetime(
        2026,
        7,
        1,
        10,
        30,
        15,
        123456,
        tzinfo=datetime_timezone.utc,
    )

    assert rpc_server._datetime_to_unix_timestamp(value) == pytest.approx(
        value.timestamp()
    )


@pytest.mark.django_db
def test_unit_status_handler_returns_empty_jobs_before_retrieval_starts(wf):
    transfer = models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation="/shared/tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, executor)

    result = server._unit_status_handler(
        None,
        None,
        {"id": str(transfer.uuid), "lang": "en"},
    )

    assert result == {"name": "(Unnamed)", "jobs": []}


@pytest.mark.parametrize(
    "payload_overrides,expected_kwargs",
    [
        pytest.param({}, {"auto_approve": True}, id="default-auto-approve"),
        pytest.param(
            {"auto_approve": False, "processing_config": "automated"},
            {"auto_approve": False, "processing_config": "automated"},
            id="explicit-no-auto-approve",
        ),
        pytest.param(
            {"idempotency_key": "transfer-submission-123"},
            {
                "auto_approve": True,
                "idempotency_key": "transfer-submission-123",
            },
            id="idempotency-key",
        ),
    ],
)
@mock.patch("archivematica.MCPServer.server.rpc_server.create_package")
def test_package_create_handler_forwards_auto_approve(
    create_package, wf, payload_overrides, expected_kwargs
):
    transfer_uuid = uuid.uuid4()
    create_package.return_value = transfer_uuid
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    shutdown_event = threading.Event()
    shutdown_event.set()
    payload = {
        "name": "TransferName",
        "type": "standard",
        "accession": "",
        "access_system_id": "",
        "path": "home/username/transfer",
        "metadata_set_id": "",
        "user_id": "1",
    }
    payload.update(payload_overrides)

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, executor)

    assert server._package_create_handler(None, None, payload) == transfer_uuid
    create_package.assert_called_once_with(
        package_queue,
        executor,
        "TransferName",
        "standard",
        "",
        "",
        "home/username/transfer",
        "",
        "1",
        wf,
        **expected_kwargs,
    )


@mock.patch("archivematica.MCPServer.server.rpc_server.create_package")
def test_package_create_handler_returns_structured_idempotency_conflict(
    create_package, wf
):
    create_package.side_effect = rpc_server.IdempotencyKeyConflictError(
        "Idempotency key has already been used with a different request."
    )
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, mock.Mock(), mock.Mock())

    result = server._package_create_handler(
        None,
        None,
        {
            "name": "TransferName",
            "type": "standard",
            "path": "home/username/transfer",
            "user_id": "1",
            "idempotency_key": "transfer-submission-123",
        },
    )

    assert result == {
        "error": True,
        "message": "Idempotency key has already been used with a different request.",
        "status_code": 422,
        "code": "idempotency_key_reused",
    }


@mock.patch("archivematica.MCPServer.server.rpc_server.create_package")
def test_package_create_handler_returns_structured_in_progress_error(
    create_package, wf
):
    create_package.side_effect = rpc_server.IdempotencyRequestInProgressError(
        "A request with this idempotency key is still in progress."
    )
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, mock.Mock(), mock.Mock())

    result = server._package_create_handler(
        None,
        None,
        {
            "name": "TransferName",
            "type": "standard",
            "path": "home/username/transfer",
            "user_id": "1",
            "idempotency_key": "transfer-submission-123",
        },
    )

    assert result == {
        "error": True,
        "message": "A request with this idempotency key is still in progress.",
        "status_code": 409,
        "code": "idempotency_key_in_progress",
    }


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
def test_units_statuses_handler_returns_processing_transfer_without_jobs(wf):
    transfer_uuid = str(uuid.uuid4())
    processing_started_at = timezone.now()
    models.Transfer.objects.create(
        uuid=transfer_uuid,
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    unit_variable = models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=transfer_uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )
    models.UnitVariable.objects.filter(pk=unit_variable.pk).update(
        createdtime=processing_started_at
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert result == [
        {
            "id": transfer_uuid,
            "uuid": transfer_uuid,
            "timestamp": pytest.approx(
                rpc_server._datetime_to_unix_timestamp(processing_started_at)
            ),
            "active": True,
            "jobs": [],
            "directory": "TransferName",
            "processing_state": "waiting_for_processing",
        }
    ]


@pytest.mark.django_db
def test_processing_transfer_timestamp_uses_earliest_processing_config(wf):
    transfer_uuid = str(uuid.uuid4())
    processing_started_at = timezone.now()
    updated_at = processing_started_at + timedelta(seconds=60)
    models.Transfer.objects.create(
        uuid=transfer_uuid,
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    first_marker = models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=transfer_uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )
    second_marker = models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=transfer_uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )
    models.UnitVariable.objects.filter(pk=first_marker.pk).update(
        createdtime=processing_started_at
    )
    models.UnitVariable.objects.filter(pk=second_marker.pk).update(
        createdtime=updated_at
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert result[0]["timestamp"] == pytest.approx(
        rpc_server._datetime_to_unix_timestamp(processing_started_at)
    )


@pytest.mark.django_db
def test_units_statuses_handler_sorts_transfers_by_timestamp_desc(wf):
    now = timezone.now()
    transfer_times = [
        ("oldest", now - timedelta(seconds=120)),
        ("newest", now),
        ("middle", now - timedelta(seconds=60)),
    ]
    transfer_uuids = {}
    for name, createdtime in transfer_times:
        transfer_uuid = str(uuid.uuid4())
        transfer_uuids[name] = transfer_uuid
        models.Transfer.objects.create(
            uuid=transfer_uuid,
            currentlocation=f"%sharedPath%tmp/tmp123/{name}",
            status=models.PACKAGE_STATUS_PROCESSING,
        )
        marker = models.UnitVariable.objects.create(
            unittype="Transfer",
            unituuid=transfer_uuid,
            variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
        )
        models.UnitVariable.objects.filter(pk=marker.pk).update(createdtime=createdtime)
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert [item["uuid"] for item in result] == [
        transfer_uuids["newest"],
        transfer_uuids["middle"],
        transfer_uuids["oldest"],
    ]


@pytest.mark.django_db
def test_units_statuses_handler_excludes_hidden_processing_transfer_without_jobs(wf):
    models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_PROCESSING,
        hidden=True,
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert result == []


@pytest.mark.django_db
def test_units_statuses_handler_excludes_unknown_transfer_without_jobs(wf):
    models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
        status=models.PACKAGE_STATUS_UNKNOWN,
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(
        None, wf, {"type": "Transfer", "lang": "en"}
    )

    assert result == []


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
