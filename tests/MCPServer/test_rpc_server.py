import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timedelta
from datetime import timezone as datetime_timezone
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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
def test_units_summary_handler_includes_dip_jobs(wf):
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(uuid=sip_uuid)
    oldest_at = timezone.now() - timedelta(minutes=2)
    started_at = timezone.now() - timedelta(minutes=1)
    latest_at = timezone.now()
    models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitSIP",
        jobtype="Move to processing directory",
        directory=f"/shared/currentlyProcessing/summary-{sip_uuid}/",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=oldest_at,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitSIP",
        jobtype="Assign file UUIDs to objects",
        microservicegroup=rpc_server.INGEST_START_TIME_MARKER_GROUP,
        directory=f"/shared/currentlyProcessing/summary-{sip_uuid}/",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=started_at,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    latest_job = models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitDIP",
        directory=f"/shared/currentlyProcessing/summary-{sip_uuid}/",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=latest_at,
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()
    link = wf.get_link(TASK_PRODUCING_LINK_ID)

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_summary_handler(None, None, {"type": "SIP", "lang": "en"})

    assert response == [
        {
            "uuid": sip_uuid,
            "directory": "summary",
            "timestamp": pytest.approx(latest_at.timestamp()),
            "started_at": pytest.approx(started_at.timestamp()),
            "active": False,
            "status": {
                "currentstep": models.Job.STATUS_AWAITING_DECISION,
                "type": link.get_label("description", "en"),
                "microservicegroup": link.get_label("group", "en"),
            },
            "has_awaiting_decision": True,
            "awaiting_job_uuids": [str(latest_job.jobuuid)],
            "access_system_id": None,
        }
    ]
    assert "jobs" not in response[0]
    assert response[0]["status"] is not None
    assert str(latest_job.jobuuid)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("unit_type", "model", "job_types", "other_job_type", "query_count"),
    [
        ("Transfer", models.Transfer, ["unitTransfer"], "unitDIP", 2),
        ("SIP", models.SIP, ["unitSIP", "unitDIP"], "unitTransfer", 3),
    ],
)
@pytest.mark.parametrize("unit_count", [1, 12])
def test_units_summary_batches_current_decision_identities(
    wf, unit_type, model, job_types, other_job_type, query_count, unit_count
):
    created_at = timezone.now()
    expected = {}
    for index in range(unit_count):
        unit = model.objects.create(uuid=uuid.uuid4())
        pending = []
        for offset, job_type, status in [
            (3, job_types[-1], models.Job.STATUS_AWAITING_DECISION),
            (1, job_types[0], models.Job.STATUS_AWAITING_DECISION),
            (90, job_types[0], models.Job.STATUS_EXECUTING_COMMANDS),
            (2, job_types[0], models.Job.STATUS_COMPLETED_SUCCESSFULLY),
            (99, other_job_type, models.Job.STATUS_AWAITING_DECISION),
        ]:
            job = models.Job.objects.create(
                jobuuid=uuid.UUID(int=index * 100 + offset),
                sipuuid=unit.pk,
                unittype=job_type,
                microservicechainlink=TASK_PRODUCING_LINK_ID,
                createdtime=created_at,
                currentstep=status,
            )
            if status == models.Job.STATUS_AWAITING_DECISION and job_type in job_types:
                pending.append(str(job.jobuuid))
        expected[str(unit.pk)] = sorted(pending)

    hidden = model.objects.create(uuid=uuid.uuid4(), hidden=True)
    models.Job.objects.create(
        sipuuid=hidden.pk,
        unittype=job_types[0],
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=created_at,
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, mock.MagicMock(), None)
    payload = {"type": unit_type, "lang": "en"}

    with CaptureQueriesContext(connection) as queries:
        response = server._units_summary_handler(None, None, payload)

    assert len(queries) == query_count
    assert {row["uuid"]: row["awaiting_job_uuids"] for row in response} == expected
    assert all(row["has_awaiting_decision"] for row in response)

    # A different decision can become current without changing either the
    # latest Job timestamp or the boolean flag. Its identity must change the
    # response so the HTTP client's unchanged-body optimization sees it.
    unit_id = response[0]["uuid"]
    old_job_id = expected[unit_id][0]
    models.Job.objects.filter(pk=old_job_id).update(
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY
    )
    replacement_id = uuid.UUID(int=uuid.UUID(old_job_id).int + 3)
    models.Job.objects.create(
        jobuuid=replacement_id,
        sipuuid=unit_id,
        unittype=job_types[0],
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=created_at,
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    expected_row = dict(response[0])
    expected_row["awaiting_job_uuids"] = sorted(
        [expected[unit_id][1], str(replacement_id)]
    )
    updated = server._units_summary_handler(None, None, payload)
    assert next(row for row in updated if row["uuid"] == unit_id) == expected_row


@pytest.mark.django_db
def test_units_summary_handler_returns_queued_transfer_without_jobs(wf):
    transfer_uuid = str(uuid.uuid4())
    processing_started_at = timezone.now()
    models.Transfer.objects.create(
        uuid=transfer_uuid,
        currentlocation=f"%sharedPath%tmp/{transfer_uuid}/QueuedTransfer",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    marker = models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=transfer_uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )
    models.UnitVariable.objects.filter(pk=marker.pk).update(
        createdtime=processing_started_at
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_summary_handler(
        None, None, {"type": "Transfer", "lang": "en"}
    )

    assert response == [
        {
            "uuid": transfer_uuid,
            "directory": "QueuedTransfer",
            "timestamp": pytest.approx(processing_started_at.timestamp()),
            "started_at": pytest.approx(processing_started_at.timestamp()),
            "active": True,
            "status": None,
            "has_awaiting_decision": False,
            "awaiting_job_uuids": [],
            "processing_state": "waiting_for_processing",
        }
    ]


@pytest.mark.django_db
def test_unit_job_groups_handler_aggregates_repeated_jobs(wf):
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(uuid=sip_uuid)
    started_at = timezone.now() - timedelta(minutes=2)
    jobs = []
    for job_id, offset, unit_type in (
        (3, 0, "unitSIP"),
        (1, 2, "unitSIP"),
        (2, 2, "unitDIP"),
    ):
        jobs.append(
            models.Job.objects.create(
                jobuuid=uuid.UUID(int=job_id),
                sipuuid=sip.pk,
                unittype=unit_type,
                microservicechainlink=TASK_PRODUCING_LINK_ID,
                createdtime=started_at + timedelta(seconds=offset),
                currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            )
        )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()
    link = wf.get_link(TASK_PRODUCING_LINK_ID)

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    with CaptureQueriesContext(connection) as queries:
        response = server._unit_job_groups_handler(
            None,
            None,
            {"type": "SIP", "id": sip_uuid, "lang": "en"},
        )

    # Correct results and query counts cannot catch a representative subquery
    # evaluated for every input Job. It must not become a third grouping key.
    (aggregate_sql,) = (
        query["sql"] for query in queries if " GROUP BY " in query["sql"]
    )
    group_by = aggregate_sql.rsplit(" GROUP BY ", 1)[1].split(" ORDER BY ", 1)[0]
    assert group_by == "1, 2"

    assert response == [
        {
            "name": link.get_label("group", "en"),
            "jobs": [
                {
                    "key": (
                        f"{TASK_PRODUCING_LINK_ID}:"
                        f"{models.Job.STATUS_COMPLETED_SUCCESSFULLY}"
                    ),
                    "link_id": TASK_PRODUCING_LINK_ID,
                    "currentstep": models.Job.STATUS_COMPLETED_SUCCESSFULLY,
                    "timestamp": pytest.approx(
                        (started_at + timedelta(seconds=2)).timestamp()
                    ),
                    "first_timestamp": pytest.approx(started_at.timestamp()),
                    "microservicegroup": link.get_label("group", "en"),
                    "type": link.get_label("description", "en"),
                    "count": 3,
                    "uuid": str(jobs[-1].jobuuid),
                    "produces_tasks": True,
                }
            ],
        }
    ]


@pytest.mark.django_db
def test_unit_job_groups_handler_scopes_representatives_by_unit_and_status(wf):
    sip = models.SIP.objects.create(uuid=uuid.uuid4())
    other_sip = models.SIP.objects.create(uuid=uuid.uuid4())
    started_at = timezone.now() - timedelta(minutes=2)
    jobs_by_status = {}
    for offset, status in enumerate(
        (models.Job.STATUS_COMPLETED_SUCCESSFULLY, models.Job.STATUS_FAILED)
    ):
        jobs_by_status[status] = models.Job.objects.create(
            sipuuid=sip.pk,
            unittype="unitSIP",
            microservicechainlink=TASK_PRODUCING_LINK_ID,
            createdtime=started_at + timedelta(seconds=offset),
            currentstep=status,
        )
    for unit_id, unit_type in (
        (other_sip.pk, "unitSIP"),
        (sip.pk, "unitTransfer"),
    ):
        models.Job.objects.create(
            sipuuid=unit_id,
            unittype=unit_type,
            microservicechainlink=TASK_PRODUCING_LINK_ID,
            createdtime=started_at + timedelta(seconds=2),
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)

    response = server._unit_job_groups_handler(
        None,
        None,
        {"type": "SIP", "id": str(sip.pk), "lang": "en"},
    )

    assert len(response) == 1
    rows = response[0]["jobs"]
    assert len(rows) == 2
    assert {row["currentstep"]: (row["uuid"], row["count"]) for row in rows} == {
        status: (str(job.jobuuid), 1) for status, job in jobs_by_status.items()
    }


@pytest.mark.django_db
def test_unit_job_groups_handler_includes_dip_decisions(wf):
    sip_uuid = str(uuid.uuid4())
    sip = models.SIP.objects.create(uuid=sip_uuid)
    waiting_job = models.Job.objects.create(
        sipuuid=sip.pk,
        unittype="unitDIP",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=timezone.now(),
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    choice = mock.Mock()
    choice.get_choices.return_value = {"approve": {"en": "Approve"}}
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {
        str(waiting_job.jobuuid): choice
    }
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._unit_job_groups_handler(
        None,
        None,
        {"type": "SIP", "id": sip_uuid, "lang": "en"},
    )

    row = response[0]["jobs"][0]
    assert row["uuid"] == str(waiting_job.jobuuid)
    assert row["count"] == 1
    assert row["choices"] == {"approve": "Approve"}
    assert row["produces_tasks"] is True


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
