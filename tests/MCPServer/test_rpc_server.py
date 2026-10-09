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
from archivematica.MCPServer.server.workflow import Workflow
from tests.factories import JobFactory
from tests.factories import SIPFactory
from tests.factories import TransferFactory

TASK_PRODUCING_LINK_ID = "002716a1-ae29-4f36-98ab-0d97192669c4"
FAILED_TRANSFER_TERMINAL_LINK_ID = "377f8ebb-7989-4a68-9361-658079ff8138"
FAILED_SIP_TERMINAL_LINK_ID = "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c"


@pytest.fixture
def processing_configuration(
    processing_transfer: models.Transfer,
) -> models.UnitVariable:
    """The processing configuration marker of the processing transfer, which
    records when its processing started.
    """
    return models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=processing_transfer.uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )


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
def test_unit_status_handler_returns_empty_jobs_before_retrieval_starts(
    wf: Workflow, processing_transfer: models.Transfer
) -> None:
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    shutdown_event = threading.Event()
    shutdown_event.set()
    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, executor)

    result = server._unit_status_handler(
        None,
        None,
        {"id": str(processing_transfer.uuid), "lang": "en"},
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
def test_approve_partial_reingest_handler(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    make_job(
        sip,
        microservicegroup="Reingest AIP",
        currentstep=models.Job.STATUS_AWAITING_DECISION,
    )
    package_queue = mock.MagicMock()
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    server._approve_partial_reingest_handler(None, wf, {"sip_uuid": sip.pk})

    package_queue.decide.assert_called_once()


@pytest.mark.django_db
def test_units_statuses_handler_sets_produces_tasks_from_job_class(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    task_producing_link = wf.get_link(TASK_PRODUCING_LINK_ID)
    assert get_job_class_for_link(task_producing_link).produces_tasks is True

    make_job(
        sip,
        microservicegroup="Test group",
        microservicechainlink=task_producing_link.id,
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
def test_units_summary_handler_includes_dip_jobs(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    directory = f"/shared/currentlyProcessing/summary-{sip.uuid}/"
    oldest_at = timezone.now() - timedelta(minutes=2)
    started_at = timezone.now() - timedelta(minutes=1)
    latest_at = timezone.now()
    make_job(
        sip,
        jobtype="Move to processing directory",
        directory=directory,
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=oldest_at,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    make_job(
        sip,
        jobtype="Assign file UUIDs to objects",
        microservicegroup=rpc_server.INGEST_START_TIME_MARKER_GROUP,
        directory=directory,
        microservicechainlink=TASK_PRODUCING_LINK_ID,
        createdtime=started_at,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    latest_job = make_job(
        sip,
        unittype="unitDIP",
        directory=directory,
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
            "uuid": str(sip.uuid),
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
    wf: Workflow,
    make_job: JobFactory,
    unit_type: str,
    model: type[models.Transfer] | type[models.SIP],
    job_types: list[str],
    other_job_type: str,
    query_count: int,
    unit_count: int,
) -> None:
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
            job = make_job(
                unit,
                jobuuid=uuid.UUID(int=index * 100 + offset),
                unittype=job_type,
                microservicechainlink=TASK_PRODUCING_LINK_ID,
                createdtime=created_at,
                currentstep=status,
            )
            if status == models.Job.STATUS_AWAITING_DECISION and job_type in job_types:
                pending.append(str(job.jobuuid))
        expected[str(unit.pk)] = sorted(pending)

    hidden = model.objects.create(uuid=uuid.uuid4(), hidden=True)
    make_job(
        hidden,
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
    make_job(
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
def test_units_summary_handler_returns_queued_transfer_without_jobs(
    wf: Workflow,
    processing_transfer: models.Transfer,
    processing_configuration: models.UnitVariable,
) -> None:
    processing_started_at = timezone.now()
    models.UnitVariable.objects.filter(pk=processing_configuration.pk).update(
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
            "uuid": str(processing_transfer.uuid),
            "directory": "TransferName",
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
def test_units_summary_handler_returns_failed_transfer_without_jobs(
    wf: Workflow,
    processing_transfer: models.Transfer,
    processing_configuration: models.UnitVariable,
) -> None:
    processing_started_at = timezone.now() - timedelta(minutes=1)
    completed_at = timezone.now()
    processing_transfer.status = models.PACKAGE_STATUS_FAILED
    processing_transfer.completed_at = completed_at
    processing_transfer.save()
    models.UnitVariable.objects.filter(pk=processing_configuration.pk).update(
        createdtime=processing_started_at
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    with mock.patch.object(
        rpc_server,
        "_",
        side_effect=lambda message: (
            f"{rpc_server.translation.get_language()}:{message}"
        ),
    ):
        response = server._units_summary_handler(
            None, None, {"type": "Transfer", "lang": "es"}
        )

    assert response == [
        {
            "uuid": str(processing_transfer.uuid),
            "directory": "TransferName",
            "timestamp": pytest.approx(completed_at.timestamp()),
            "started_at": pytest.approx(processing_started_at.timestamp()),
            "active": False,
            "status": {
                "currentstep": models.Job.STATUS_FAILED,
                "type": "es:Failed before processing started",
                "microservicegroup": "",
            },
            "has_awaiting_decision": False,
            "awaiting_job_uuids": [],
        }
    ]


@pytest.mark.parametrize(
    ("unit_type", "model_class", "job_unit_type", "failure_link_id"),
    (
        (
            "Transfer",
            models.Transfer,
            "unitTransfer",
            FAILED_TRANSFER_TERMINAL_LINK_ID,
        ),
        ("SIP", models.SIP, "unitSIP", FAILED_SIP_TERMINAL_LINK_ID),
    ),
)
@pytest.mark.django_db
def test_units_summary_handler_returns_declared_failure_status(
    wf: Workflow,
    make_job: JobFactory,
    unit_type: str,
    model_class: type[models.Transfer] | type[models.SIP],
    job_unit_type: str,
    failure_link_id: str,
) -> None:
    unit_uuid = str(uuid.uuid4())
    unit = model_class.objects.create(
        uuid=unit_uuid,
        status=models.PACKAGE_STATUS_DONE,
    )
    latest_at = timezone.now()
    make_job(
        unit,
        unittype=job_unit_type,
        directory=f"/shared/failed/{unit_uuid}/FailedPackage/",
        microservicechainlink=failure_link_id,
        createdtime=latest_at,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()
    link = wf.get_link(failure_link_id)

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    response = server._units_summary_handler(
        None, None, {"type": unit_type, "lang": "en"}
    )

    assert len(response) == 1
    assert response[0]["uuid"] == unit_uuid
    assert response[0]["directory"] == "FailedPackage"
    assert response[0]["timestamp"] == pytest.approx(latest_at.timestamp())
    assert response[0]["status"] == {
        "currentstep": models.Job.STATUS_FAILED,
        "type": link.get_label("description", "en"),
        "microservicegroup": link.get_label("group", "en"),
    }


@pytest.mark.django_db
def test_unit_job_groups_handler_aggregates_repeated_jobs(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    started_at = timezone.now() - timedelta(minutes=2)
    jobs = []
    for job_id, offset, unit_type in (
        (3, 0, "unitSIP"),
        (1, 2, "unitSIP"),
        (2, 2, "unitDIP"),
    ):
        jobs.append(
            make_job(
                sip,
                jobuuid=uuid.UUID(int=job_id),
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
            {"type": "SIP", "id": str(sip.uuid), "lang": "en"},
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
def test_unit_job_groups_handler_scopes_representatives_by_unit_and_status(
    wf: Workflow, sip: models.SIP, make_sip: SIPFactory, make_job: JobFactory
) -> None:
    other_sip = make_sip()
    started_at = timezone.now() - timedelta(minutes=2)
    jobs_by_status = {}
    for offset, status in enumerate(
        (models.Job.STATUS_COMPLETED_SUCCESSFULLY, models.Job.STATUS_FAILED)
    ):
        jobs_by_status[status] = make_job(
            sip,
            microservicechainlink=TASK_PRODUCING_LINK_ID,
            createdtime=started_at + timedelta(seconds=offset),
            currentstep=status,
        )
    for unit_id, unit_type in (
        (other_sip.pk, "unitSIP"),
        (sip.pk, "unitTransfer"),
    ):
        make_job(
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
def test_unit_job_groups_handler_includes_dip_decisions(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    waiting_job = make_job(
        sip,
        unittype="unitDIP",
        microservicechainlink=TASK_PRODUCING_LINK_ID,
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
        {"type": "SIP", "id": str(sip.uuid), "lang": "en"},
    )

    row = response[0]["jobs"][0]
    assert row["uuid"] == str(waiting_job.jobuuid)
    assert row["count"] == 1
    assert row["choices"] == {"approve": "Approve"}
    assert row["produces_tasks"] is True


@pytest.mark.django_db
def test_units_statuses_handler_returns_transfers(
    wf: Workflow, transfer: models.Transfer, make_job: JobFactory
) -> None:
    make_job(
        transfer,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink=TASK_PRODUCING_LINK_ID,
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
    assert result[0]["uuid"] == str(transfer.uuid)


@pytest.mark.django_db
def test_units_statuses_handler_returns_processing_transfer_without_jobs(
    wf: Workflow,
    processing_transfer: models.Transfer,
    processing_configuration: models.UnitVariable,
) -> None:
    processing_started_at = timezone.now()
    models.UnitVariable.objects.filter(pk=processing_configuration.pk).update(
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
            "id": str(processing_transfer.uuid),
            "uuid": str(processing_transfer.uuid),
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
def test_processing_transfer_timestamp_uses_earliest_processing_config(
    wf: Workflow,
    processing_transfer: models.Transfer,
    processing_configuration: models.UnitVariable,
) -> None:
    processing_started_at = timezone.now()
    updated_at = processing_started_at + timedelta(seconds=60)
    second_marker = models.UnitVariable.objects.create(
        unittype="Transfer",
        unituuid=processing_transfer.uuid,
        variable=models.UNIT_VARIABLE_PROCESSING_CONFIGURATION,
    )
    models.UnitVariable.objects.filter(pk=processing_configuration.pk).update(
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
def test_units_statuses_handler_sorts_transfers_by_timestamp_desc(
    wf: Workflow, make_transfer: TransferFactory
) -> None:
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
        make_transfer(
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
def test_units_statuses_handler_excludes_hidden_processing_transfer_without_jobs(
    wf: Workflow, processing_transfer: models.Transfer
) -> None:
    processing_transfer.hidden = True
    processing_transfer.save()
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
def test_units_statuses_handler_excludes_unknown_transfer_without_jobs(
    wf: Workflow, transfer: models.Transfer
) -> None:
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
def test_units_statuses_handler_returns_sips(
    wf: Workflow, sip: models.SIP, make_job: JobFactory
) -> None:
    make_job(
        sip,
        currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        microservicechainlink=TASK_PRODUCING_LINK_ID,
    )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(None, wf, {"type": "SIP", "lang": "en"})

    assert len(result) == 1
    assert result[0]["uuid"] == str(sip.uuid)


@pytest.mark.django_db
def test_units_statuses_handler_excludes_hidden_transfers(
    wf: Workflow,
    transfer: models.Transfer,
    make_transfer: TransferFactory,
    make_job: JobFactory,
) -> None:
    for unit in [transfer, make_transfer(hidden=True)]:
        make_job(
            unit,
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            microservicechainlink=TASK_PRODUCING_LINK_ID,
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
    assert result[0]["uuid"] == str(transfer.uuid)


@pytest.mark.django_db
def test_units_statuses_handler_excludes_hidden_sips(
    wf: Workflow, sip: models.SIP, make_sip: SIPFactory, make_job: JobFactory
) -> None:
    for unit in [sip, make_sip(hidden=True)]:
        make_job(
            unit,
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            microservicechainlink=TASK_PRODUCING_LINK_ID,
        )
    package_queue = mock.MagicMock()
    package_queue.jobs_awaiting_decisions.return_value = {}
    shutdown_event = threading.Event()
    shutdown_event.set()

    server = rpc_server.RPCServer(wf, shutdown_event, package_queue, None)
    result = server._units_statuses_handler(None, wf, {"type": "SIP", "lang": "en"})

    assert len(result) == 1
    assert result[0]["uuid"] == str(sip.uuid)


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
