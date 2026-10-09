import datetime
import json
import pathlib
import uuid
from collections.abc import Callable
from unittest import mock

import pytest
import pytest_django
from django.test import Client
from django.urls import reverse
from django.utils.timezone import make_aware
from lxml import etree

from archivematica.archivematicaCommon import archivematicaFunctions
from archivematica.archivematicaCommon.processing import install_builtin_config
from archivematica.dashboard.components import helpers
from archivematica.dashboard.components.api import views
from archivematica.dashboard.main.models import PACKAGE_STATUS_COMPLETED_SUCCESSFULLY
from archivematica.dashboard.main.models import PACKAGE_STATUS_FAILED
from archivematica.dashboard.main.models import PACKAGE_STATUS_PROCESSING
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import DublinCore
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Job
from archivematica.dashboard.main.models import RightsStatement
from archivematica.dashboard.main.models import Task
from archivematica.dashboard.main.models import Transfer
from tests.factories import DublinCoreFactory
from tests.factories import JobFactory
from tests.factories import RightsStatementFactory
from tests.factories import SIPFactory
from tests.factories import TaskFactory
from tests.factories import TransferFactory


@pytest.fixture
def jobs_processing(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Examine contents",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T22:50:56Z",
            jobtype="Examine contents?",
        ),
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T22:50:57Z",
            jobtype="Load options to create SIPs",
        ),
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_EXECUTING_COMMANDS,
            createdtime="2016-10-04T22:50:57Z",
            jobtype="Check transfer directory for objects",
        ),
    ]


@pytest.fixture
def retrieval_job(make_job: JobFactory, transfer: Transfer) -> Callable[[int], Job]:
    """Create a retrieval job in the requested lifecycle state."""

    def make(status: int) -> Job:
        return make_job(
            transfer,
            jobtype="Retrieve transfer source",
            microservicegroup="Retrieve transfer source",
            microservicechainlink=views.TRANSFER_SOURCE_RETRIEVAL_LINK_ID,
            currentstep=status,
            createdtime=make_aware(datetime.datetime(2026, 6, 21)),
        )

    return make


@pytest.fixture
def jobs_user_input(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_AWAITING_DECISION,
            createdtime="2016-10-04T22:50:58Z",
            jobtype="Create SIP(s)",
        )
    ]


@pytest.fixture
def jobs_failed(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Failed transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-05T00:10:54Z",
            jobtype="Move to the failed directory",
        )
    ]


@pytest.fixture
def jobs_rejected(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Reject transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:48:27Z",
            jobtype="Move to the rejected directory",
        )
    ]


@pytest.fixture
def jobs_transfer_complete(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:05:55Z",
            jobtype="Create SIP from transfer objects",
        ),
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:05:56Z",
            jobtype="Move to SIP creation directory for completed transfers",
        ),
    ]


@pytest.fixture
def jobs_transfer_backlog(make_job: JobFactory, transfer: Transfer) -> list[Job]:
    return [
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:40:12Z",
            jobtype="Move transfer to backlog",
        ),
        make_job(
            transfer,
            microservicegroup="Create SIP from Transfer",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:40:14Z",
            jobtype="Create placement in backlog PREMIS events",
        ),
    ]


@pytest.fixture
def jobs_sip_complete(make_job: JobFactory, sip: SIP) -> list[Job]:
    return [
        make_job(
            sip,
            microservicegroup="Store AIP",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:18:46Z",
            jobtype="Remove the processing directory",
        )
    ]


@pytest.fixture
def jobs_sip_complete_cleanup_last(make_job: JobFactory, sip: SIP) -> list[Job]:
    return [
        make_job(
            sip,
            microservicegroup="Store AIP",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:18:47Z",
            jobtype="Clean up after storing AIP",
        )
    ]


@pytest.fixture
def jobs_awaiting_approval(
    make_job: JobFactory, transfer: Transfer, sip: SIP
) -> list[Job]:
    """The pending approval of the transfer and the completed storage of the SIP."""
    return [
        make_job(
            transfer,
            jobtype="Approve standard transfer",
            currentstep=Job.STATUS_AWAITING_DECISION,
            directory="%sharedPath%watchedDirectories/activeTransfers/standardTransfer/test-2/",
            createdtime=make_aware(datetime.datetime(2023, 11, 14, 9, 20)),
        ),
        make_job(
            sip,
            jobtype="Store AIP",
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            directory="%sharedPath%watchedDirectories/storeAIP/test-1/",
            createdtime=make_aware(datetime.datetime(2023, 11, 13, 0, 0)),
        ),
    ]


@pytest.mark.django_db
def test_get_unit_status_processing(jobs_processing, transfer):
    """It should return PROCESSING."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "PROCESSING"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 0


@pytest.mark.django_db
def test_get_unit_status_user_input(jobs_processing, jobs_user_input, transfer):
    """It should return USER_INPUT."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "USER_INPUT"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 0


@pytest.mark.django_db
def test_get_unit_status_failed(jobs_processing, jobs_failed, transfer):
    """It should return FAILED."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "FAILED"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 1


@pytest.mark.django_db
def test_get_unit_status_rejected(jobs_processing, jobs_rejected, transfer):
    """It should return REJECTED."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "REJECTED"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 0


@pytest.mark.django_db
def test_get_unit_status_completed_transfer(
    jobs_processing: list[Job],
    jobs_transfer_complete: list[Job],
    transfer: Transfer,
    sip: SIP,
    sip_file: File,
) -> None:
    """It should return COMPLETE and the new SIP UUID."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 3
    assert "microservice" in status
    assert status["status"] == "COMPLETE"
    assert status["sip_uuid"] == str(sip.uuid)

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 1


@pytest.mark.django_db
def test_get_unit_status_backlog(jobs_processing, jobs_transfer_backlog, transfer):
    """It should return COMPLETE and in BACKLOG."""
    status = views.get_unit_status(transfer.uuid, "unitTransfer")
    assert len(status) == 3
    assert "microservice" in status
    assert status["status"] == "COMPLETE"
    assert status["sip_uuid"] == "BACKLOG"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 1


@pytest.mark.django_db
def test_get_unit_status_completed_sip(
    transfer: Transfer,
    sip: SIP,
    jobs_processing: list[Job],
    jobs_transfer_complete: list[Job],
    jobs_sip_complete: list[Job],
    sip_file: File,
) -> None:
    """It should return COMPLETE."""
    status = views.get_unit_status(sip.uuid, "unitSIP")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "COMPLETE"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 1


@pytest.mark.django_db
def test_get_unit_status_completed_sip_issue_262_workaround(
    transfer: Transfer,
    sip: SIP,
    jobs_processing: list[Job],
    jobs_transfer_complete: list[Job],
    jobs_sip_complete: list[Job],
    jobs_sip_complete_cleanup_last: list[Job],
    sip_file: File,
) -> None:
    """Test get unit status for a completed SIP when the job with the latest
    created time is not the last in the microservice chain
    (i.e, job with jobtype 'Remove the processing directory' is not the one with
    latest created time)
    It should return COMPLETE."""
    status = views.get_unit_status(sip.uuid, "unitSIP")
    assert len(status) == 2
    assert "microservice" in status
    assert status["status"] == "COMPLETE"

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )
    assert len(completed) == 1


@pytest.mark.django_db
def test_status(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    sip: SIP,
    jobs_transfer_complete: list[Job],
    sip_file: File,
) -> None:
    resp = admin_client.get(
        reverse("api:transfer_status", args=[transfer.uuid]),
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "COMPLETE"
    assert payload["type"] == "transfer"
    assert payload["uuid"] == str(transfer.uuid)


@pytest.mark.django_db
def test_status_reports_processing_before_first_retrieval_job_starts(
    admin_client, dashboard_uuid, transfer
):
    """Immediate UUID polling remains useful before PackageQueue starts a job."""
    transfer.status = PACKAGE_STATUS_PROCESSING
    transfer.currentlocation = "%sharedPath%tmp/tmp123/TransferName"
    transfer.save(update_fields=["status", "currentlocation"])

    resp = admin_client.get(reverse("api:transfer_status", args=[transfer.uuid]))

    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "PROCESSING"
    assert payload["microservice"] == "Waiting for processing to start"
    assert payload["uuid"] == str(transfer.uuid)


@pytest.mark.django_db
def test_status_remains_processing_after_retrieval_completes(
    admin_client, dashboard_uuid, transfer, retrieval_job
):
    """Retrieval success is not the same as transfer completion."""
    retrieval_job(Job.STATUS_COMPLETED_SUCCESSFULLY)

    resp = admin_client.get(reverse("api:transfer_status", args=[transfer.uuid]))

    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "PROCESSING"
    assert payload["microservice"] == "Retrieve transfer source"


@pytest.mark.django_db
def test_status_reports_failed_retrieval(
    admin_client, dashboard_uuid, transfer, retrieval_job
):
    retrieval_job(Job.STATUS_FAILED)

    resp = admin_client.get(reverse("api:transfer_status", args=[transfer.uuid]))

    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "FAILED"
    assert payload["microservice"] == "Retrieve transfer source"


@pytest.mark.django_db
def test_status_reports_failed_bootstrap_without_jobs(
    admin_client, dashboard_uuid, transfer
):
    """Bootstrap failures are visible even when no workflow job was persisted."""
    transfer.status = PACKAGE_STATUS_FAILED
    transfer.completed_at = make_aware(datetime.datetime(2026, 6, 21))
    transfer.save(update_fields=["status", "completed_at"])

    resp = admin_client.get(reverse("api:transfer_status", args=[transfer.uuid]))

    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "FAILED"
    assert payload["microservice"] == "Failed before processing started"


@pytest.mark.django_db
def test_status_transfer_not_found(admin_client, dashboard_uuid):
    transfer_uuid = uuid.uuid4()
    resp = admin_client.get(
        reverse("api:transfer_status", args=[transfer_uuid]),
    )

    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": f"Cannot fetch unitTransfer with UUID {transfer_uuid}",
        "error": True,
        "type": "transfer",
    }


@pytest.mark.django_db
def test_status_ingest_not_found(admin_client, dashboard_uuid):
    ingest_uuid = uuid.uuid4()
    resp = admin_client.get(
        reverse("api:ingest_status", args=[ingest_uuid]),
    )

    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": f"Cannot fetch unitSIP with UUID {ingest_uuid}",
        "error": True,
        "type": "SIP",
    }


@pytest.mark.django_db
def test_status_with_bogus_unit(
    admin_client: Client, dashboard_uuid: uuid.UUID, transfer: Transfer
) -> None:
    """It should return a 400 error as the status cannot be determined."""
    resp = admin_client.get(reverse("api:transfer_status", args=[transfer.uuid]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert (
        payload["message"]
        == f"Unable to determine the status of the unit {transfer.uuid}"
    )


@pytest.mark.django_db
def test_completed_units(
    transfer: Transfer, sip: SIP, jobs_transfer_complete: list[Job], sip_file: File
) -> None:
    completed = views._completed_units()
    assert completed == [str(transfer.uuid)]


@pytest.mark.django_db
def test_completed_units_with_bogus_unit(
    transfer: Transfer,
    sip: SIP,
    jobs_transfer_complete: list[Job],
    sip_file: File,
    make_transfer: TransferFactory,
) -> None:
    """Bogus units should be excluded and handled gracefully."""
    make_transfer()
    completed = views._completed_units()
    assert completed == [str(transfer.uuid)]


@pytest.mark.django_db
def test_completed_transfers(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    sip: SIP,
    jobs_transfer_complete: list[Job],
    sip_file: File,
) -> None:
    resp = admin_client.get(reverse("api:completed_transfers"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed transfers successfully.",
        "results": [str(transfer.uuid)],
    }


@pytest.mark.django_db
def test_completed_transfers_with_bogus_transfer(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    sip: SIP,
    jobs_transfer_complete: list[Job],
    sip_file: File,
    make_transfer: TransferFactory,
) -> None:
    """Bogus transfers should be excluded and handled gracefully."""
    make_transfer()
    resp = admin_client.get(reverse("api:completed_transfers"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed transfers successfully.",
        "results": [str(transfer.uuid)],
    }


@pytest.mark.django_db
def test_completed_ingests(admin_client, dashboard_uuid, sip, jobs_sip_complete):
    resp = admin_client.get(reverse("api:completed_ingests"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed ingests successfully.",
        "results": [str(sip.uuid)],
    }


@pytest.mark.django_db
def test_completed_ingests_with_bogus_sip(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    sip: SIP,
    jobs_sip_complete: list[Job],
    make_sip: SIPFactory,
) -> None:
    """Bogus ingests should be excluded and handled gracefully."""
    make_sip()
    resp = admin_client.get(reverse("api:completed_ingests"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed ingests successfully.",
        "results": [str(sip.uuid)],
    }


@pytest.mark.django_db
def test_unit_jobs_with_bogus_unit_uuid(admin_client, dashboard_uuid):
    bogus_unit_uuid = str(uuid.uuid4())
    resp = admin_client.get(reverse("api:v2beta_jobs", args=[bogus_unit_uuid]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert payload["message"] == f"No jobs found for unit: {bogus_unit_uuid}"


@pytest.mark.django_db
def test_unit_jobs(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    jobs_transfer_complete: list[Job],
    make_task: TaskFactory,
) -> None:
    # Add a task to an existing job
    task_uuid = uuid.uuid4()
    job_index = 1
    make_task(
        jobs_transfer_complete[job_index],
        taskuuid=task_uuid,
        createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 10)),
        exitcode=0,
    )
    # each payload mapping has information about the job and its tasks
    expected = []
    for job in jobs_transfer_complete:
        expected.append(
            {
                "uuid": str(job.jobuuid),
                "name": job.jobtype,
                "status": "COMPLETE",
                "microservice": job.microservicegroup,
                "link_uuid": str(job.microservicechainlink),
                "tasks": [
                    {"uuid": str(task.taskuuid), "exit_code": task.exitcode}
                    for task in job.task_set.all()
                ],
            }
        )

    resp = admin_client.get(reverse("api:v2beta_jobs", args=[transfer.uuid]))
    assert resp.status_code == 200

    # payload contains a mapping for each job
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == len(jobs_transfer_complete)
    assert payload == expected
    # check the task added before is associated to the expected job
    assert payload[job_index]["tasks"] == [{"uuid": str(task_uuid), "exit_code": 0}]


@pytest.mark.django_db
def test_unit_jobs_searching_for_microservice(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]),
        {"microservice": "Reject transfer"},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == 1
    job = payload[0]
    stored_job = jobs_rejected[0]
    assert job["uuid"] == str(stored_job.jobuuid)
    assert job["name"] == stored_job.jobtype
    assert job["status"] == "COMPLETE"
    assert job["microservice"] == stored_job.microservicegroup
    assert job["link_uuid"] == str(stored_job.microservicechainlink)
    assert job["tasks"] == [
        {"uuid": str(task.taskuuid), "exit_code": task.exitcode}
        for task in stored_job.task_set.all()
    ]


@pytest.mark.django_db
def test_unit_jobs_searching_for_microservice_with_prefix(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    # Test that microservice search also works with a "Microservice:" prefix
    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]),
        {"microservice": "Microservice: Reject transfer"},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == 1
    job = payload[0]
    assert job["uuid"] == str(jobs_rejected[0].jobuuid)


@pytest.mark.django_db
def test_unit_jobs_searching_for_chain_link(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    stored_job = jobs_rejected[0]
    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]),
        {"link_uuid": stored_job.microservicechainlink},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == 1
    job = payload[0]
    assert job["uuid"] == str(stored_job.jobuuid)
    assert job["name"] == stored_job.jobtype
    assert job["status"] == "COMPLETE"
    assert job["microservice"] == stored_job.microservicegroup
    assert job["link_uuid"] == str(stored_job.microservicechainlink)
    assert job["tasks"] == [
        {"uuid": str(task.taskuuid), "exit_code": task.exitcode}
        for task in stored_job.task_set.all()
    ]


@pytest.mark.django_db
def test_unit_jobs_searching_for_name(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]),
        {"name": "Move to the rejected directory"},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == 1
    job = payload[0]
    stored_job = jobs_rejected[0]
    assert job["uuid"] == str(stored_job.jobuuid)
    assert job["name"] == stored_job.jobtype
    assert job["status"] == "COMPLETE"
    assert job["microservice"] == stored_job.microservicegroup
    assert job["link_uuid"] == str(stored_job.microservicechainlink)
    assert job["tasks"] == [
        {"uuid": str(task.taskuuid), "exit_code": task.exitcode}
        for task in stored_job.task_set.all()
    ]


@pytest.mark.django_db
def test_unit_jobs_searching_for_name_with_prefix(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    # Test that name search also works with a "Job:" prefix
    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]),
        {"name": "Job: Move to the rejected directory"},
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert len(payload) == 1
    job = payload[0]
    assert job["uuid"] == str(jobs_rejected[0].jobuuid)


@pytest.mark.django_db
def test_unit_jobs_with_detailed_task_output(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    jobs_rejected: list[Job],
    make_task: TaskFactory,
) -> None:
    # Add a task to an existing job
    task_uuid = uuid.uuid4()
    make_task(
        jobs_rejected[0],
        taskuuid=task_uuid,
        createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 10)),
        exitcode=0,
    )
    expected = []
    for job in jobs_rejected:
        expected.append(
            {
                "uuid": str(job.jobuuid),
                "name": job.jobtype,
                "status": "COMPLETE",
                "microservice": job.microservicegroup,
                "link_uuid": str(job.microservicechainlink),
                "tasks": [
                    {
                        "uuid": str(task.taskuuid),
                        "exit_code": task.exitcode,
                        "file_uuid": task.fileuuid,
                        "file_name": task.filename,
                        "time_created": task.createdtime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "time_started": task.starttime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "time_ended": task.endtime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "duration": helpers.task_duration_in_seconds(task),
                    }
                    for task in job.task_set.all()
                ],
            }
        )

    resp = admin_client.get(
        reverse("api:v2beta_jobs", args=[transfer.uuid]), {"detailed": "true"}
    )
    assert resp.status_code == 200

    payload = json.loads(resp.content.decode("utf8"))
    assert payload == expected


@pytest.mark.django_db
def test_task_with_bogus_task_uuid(admin_client, dashboard_uuid):
    bogus_task_uuid = str(uuid.uuid4())
    resp = admin_client.get(reverse("api:v2beta_task", args=[bogus_task_uuid]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert payload["message"] == f"Task with UUID {bogus_task_uuid} does not exist"


@pytest.mark.django_db
def test_task(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    jobs_transfer_complete: list[Job],
    make_task: TaskFactory,
) -> None:
    stored_job = jobs_transfer_complete[1]
    # fixtures don't have any tasks
    task_uuid = uuid.uuid4()
    make_task(
        stored_job,
        taskuuid=task_uuid,
        createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 0)),
        starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 0)),
        endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 5)),
        exitcode=0,
    )
    resp = admin_client.get(reverse("api:v2beta_task", args=[task_uuid]))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    # payload is a mapping of task attributes
    assert payload["uuid"] == str(task_uuid)
    assert payload["exit_code"] == 0
    assert payload["file_uuid"] is None
    assert payload["file_name"] == ""
    assert payload["time_created"] == "2019-06-18T00:00:00"
    assert payload["time_started"] == "2019-06-18T00:00:00"
    assert payload["time_ended"] == "2019-06-18T00:00:05"
    assert payload["duration"] == 5


@pytest.fixture
def builtin_processing_configurations(
    processing_configurations_path: pathlib.Path,
) -> pathlib.Path:
    """The processing configurations directory with the built-in configurations."""
    install_builtin_config("default")
    install_builtin_config("automated")

    return processing_configurations_path


@pytest.mark.django_db
def test_list_processing_configs(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    builtin_processing_configurations: pathlib.Path,
) -> None:
    expected_names = sorted(["default", "automated"])
    response = admin_client.get(reverse("api:processing_configuration_list"))
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf8"))
    shared_dir = payload["processing_configurations"]
    assert len(shared_dir) == 2
    assert all(
        actual == expected for actual, expected in zip(shared_dir, expected_names)
    )


@pytest.mark.django_db
def test_get_existing_processing_config(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    builtin_processing_configurations: pathlib.Path,
) -> None:
    response = admin_client.get(
        reverse("api:processing_configuration", args=["default"]),
        HTTP_ACCEPT="xml",
    )
    assert response.status_code == 200
    assert etree.fromstring(response.content).xpath(".//preconfiguredChoice")


@pytest.mark.django_db
def test_delete_and_regenerate(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    builtin_processing_configurations: pathlib.Path,
) -> None:
    processing_configs = builtin_processing_configurations

    response = admin_client.delete(
        reverse("api:processing_configuration", args=["default"])
    )
    assert response.status_code == 200
    assert not (processing_configs / "defaultProcessingMCP.xml").exists()

    response = admin_client.get(
        reverse("api:processing_configuration", args=["default"]),
        HTTP_ACCEPT="xml",
    )
    assert response.status_code == 200
    assert etree.fromstring(response.content).xpath(".//preconfiguredChoice")
    assert (processing_configs / "defaultProcessingMCP.xml").exists()


@pytest.mark.django_db
def test_404_for_non_existent_config(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    builtin_processing_configurations: pathlib.Path,
) -> None:
    response = admin_client.get(
        reverse("api:processing_configuration", args=["nonexistent"]),
        HTTP_ACCEPT="xml",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_404_for_delete_non_existent_config(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    builtin_processing_configurations: pathlib.Path,
) -> None:
    response = admin_client.delete(
        reverse("api:processing_configuration", args=["nonexistent"])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_unit_status_multiple(
    jobs_failed: list[Job],
    jobs_transfer_complete: list[Job],
    jobs_rejected: list[Job],
    jobs_user_input: list[Job],
    jobs_transfer_backlog: list[Job],
    make_transfer: TransferFactory,
) -> None:
    """When the database contains 5 units of the following types:
    1. a failed transfer
    2. a completed transfer
    3. a rejected transfer
    4. a transfer awaiting user input
    5. a transfer in backlog
    then ``completed_units_efficient`` should return 3: the failed,
    the completed, and the in-backlog transfer.
    """
    failed_transfer = make_transfer()
    for job in jobs_failed:
        job.sipuuid = failed_transfer.uuid
        job.save()

    complete_transfer = make_transfer()
    for job in jobs_transfer_complete:
        job.sipuuid = complete_transfer.uuid
        job.save()

    rejected_transfer = make_transfer()
    for job in jobs_rejected:
        job.sipuuid = rejected_transfer.uuid
        job.save()

    awaiting_transfer = make_transfer()
    for job in jobs_user_input:
        job.sipuuid = awaiting_transfer.uuid
        job.save()

    backlog_transfer = make_transfer()
    for job in jobs_transfer_backlog:
        job.sipuuid = backlog_transfer.uuid
        job.save()

    expected_uuids = [
        str(t.uuid) for t in [failed_transfer, complete_transfer, backlog_transfer]
    ]

    completed = helpers.completed_units_efficient(
        unit_type="transfer", include_failed=True
    )

    assert set(completed) == set(expected_uuids)


@pytest.mark.django_db
@mock.patch(
    "archivematica.dashboard.components.api.views.authenticate_request",
    return_value=None,
)
@mock.patch(
    "archivematica.dashboard.components.filesystem_ajax.views._copy_from_transfer_sources",
    return_value=(None, ""),
)
def test_copy_metadata_files_api(
    _copy_from_transfer_sources: mock.Mock,
    authenticate_request: mock.Mock,
    make_sip: SIPFactory,
) -> None:
    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    make_sip(
        uuid=sip_uuid,
        currentpath=f"%sharedPath%more/path/metadataReminder/mysip-{sip_uuid}/",
    )

    # Call the endpoint with a mocked request
    request = mock.Mock(
        **{
            "POST.get.return_value": sip_uuid,
            "POST.getlist.return_value": [
                archivematicaFunctions.b64encode_string("locationuuid:/some/path")
            ],
            "method": "POST",
        }
    )
    result = views.copy_metadata_files_api(request)

    # Verify the contents of the response
    assert result.status_code == 201
    assert result["Content-Type"] == "application/json"
    assert json.loads(result.content) == {
        "message": "Metadata files added successfully.",
        "error": None,
    }


@pytest.mark.django_db
@mock.patch(
    "archivematica.dashboard.components.filesystem_ajax.views.start_transfer",
    return_value={},
)
def test_start_transfer_api_decodes_paths(
    start_transfer_view, admin_client, dashboard_uuid
):
    admin_client.post(
        reverse("api:start_transfer"),
        {
            "name": "my transfer",
            "type": "zipfile",
            "accession": "my accession",
            "access_system_id": "system id",
            "paths[]": [archivematicaFunctions.b64encode_string("/a/path")],
            "row_ids[]": ["row1"],
        },
    )
    start_transfer_view.assert_called_once_with(
        "my transfer", "zipfile", "my accession", "system id", ["/a/path"], ["row1"]
    )


@pytest.mark.django_db
@mock.patch(
    "archivematica.dashboard.contrib.mcp.client.gearman.JOB_COMPLETE",
)
@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_reingest_approve(gearman_client, job_complete, admin_client, dashboard_uuid):
    gearman_client.return_value = mock.Mock(
        **{
            "submit_job.return_value": mock.Mock(
                state=job_complete,
                result=None,
            )
        }
    )

    response = admin_client.post(
        reverse("api:reingest_approve"),
        {
            "uuid": "sip-uuid",
        },
    )

    assert (
        json.loads(response.content.decode("utf8")).get("message")
        == "Approval successful."
    )


@pytest.mark.django_db
def test_unapproved_transfers(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    jobs_awaiting_approval: list[Job],
) -> None:
    response = admin_client.get(reverse("api:unapproved_transfers"))
    assert response.status_code == 200

    # Verify the awaiting transfer is listed.
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "message": "Fetched unapproved transfers successfully.",
        "results": [
            {
                "directory": "test-2",
                "type": "standard",
                "uuid": str(transfer.uuid),
            }
        ],
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "post_data,expected_error",
    [
        ({}, "Please specify a transfer directory."),
        ({"directory": "mytransfer", "type": ""}, "Please specify a transfer type."),
        ({"directory": "mytransfer", "type": "bogus"}, "Invalid transfer type."),
        (
            {"directory": "mytransfer", "type": "standard"},
            "Unable to start the transfer.",
        ),
    ],
    ids=[
        "no_transfer_directory",
        "no_transfer_type",
        "invalid_transfer_type",
        "mcpclient_error",
    ],
)
@mock.patch(
    "archivematica.dashboard.contrib.mcp.client.GearmanClient", side_effect=Exception()
)
def test_approve_transfer_failures(
    gearman_client, post_data, expected_error, admin_client, dashboard_uuid
):
    response = admin_client.post(reverse("api:approve_transfer"), post_data)

    assert response.status_code == 500
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"error": True, "message": expected_error}


@pytest.mark.django_db
@mock.patch("archivematica.dashboard.contrib.mcp.client.gearman.JOB_COMPLETE")
@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_approve_transfer(gearman_client, job_complete, admin_client, dashboard_uuid):
    # Simulate a dashboard <-> Gearman <-> MCPServer interaction.
    # The MCPServer approveTransferByPath RPC method returns a UUID.
    transfer_uuid = uuid.uuid4()

    gearman_client.return_value = mock.Mock(
        **{
            "submit_job.return_value": mock.Mock(
                state=job_complete,
                result=transfer_uuid,
            )
        }
    )

    response = admin_client.post(
        reverse("api:approve_transfer"), {"directory": "mytransfer", "type": "standard"}
    )
    assert response.status_code == 200

    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"message": "Approval successful.", "uuid": str(transfer_uuid)}


@pytest.mark.django_db
def test_waiting_for_user_input(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    jobs_awaiting_approval: list[Job],
) -> None:
    response = admin_client.get(reverse("api:waiting_for_user_input"))
    assert response.status_code == 200

    # Verify the awaiting transfer is listed.
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "message": "Fetched units successfully.",
        "results": [
            {
                "microservice": "Approve standard transfer",
                "sip_directory": "test-2",
                "sip_name": "test-2",
                "sip_uuid": str(transfer.uuid),
            }
        ],
    }


@pytest.mark.django_db
def test_reingest_fails_with_missing_parameters(admin_client, dashboard_uuid):
    response = admin_client.post(
        reverse("api:transfer_reingest", kwargs={"target": "transfer"}), {}
    )

    assert response.status_code == 400
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"error": True, "message": '"name" and "uuid" are required.'}


@pytest.fixture
def sip_path(
    settings: pytest_django.Settings, shared_directory_path: pathlib.Path
) -> pathlib.Path:
    """A transfer in the temporary directory of the shared directory, which has
    the watched directories of a reingest.
    """
    for directory in [
        ("watchedDirectories", "activeTransfers", "standardTransfer"),
        ("watchedDirectories", "system", "reingestAIP"),
    ]:
        shared_directory_path.joinpath(*directory).mkdir(parents=True)

    result = shared_directory_path / "tmp" / f"mytransfer-{uuid.uuid4()}"
    result.mkdir()
    (result / "myfile.txt").write_text("my file")

    return result


@pytest.mark.django_db
def test_reingest_deletes_existing_models_related_to_sip(
    sip_path: pathlib.Path,
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    make_transfer: TransferFactory,
    make_sip: SIPFactory,
    make_job: JobFactory,
    make_task: TaskFactory,
    make_rights_statement: RightsStatementFactory,
    make_dublincore: DublinCoreFactory,
) -> None:
    transfer_uuid = sip_path.name[-36:]

    # Create a Transfer and related models.
    transfer = make_transfer(uuid=transfer_uuid)
    job = make_job(
        transfer, createdtime=make_aware(datetime.datetime(2023, 11, 15, 8, 30))
    )
    make_task(job, createdtime=make_aware(datetime.datetime(2023, 11, 15, 8, 30)))
    make_sip(uuid=transfer.uuid)
    make_rights_statement("transfer", transfer.uuid)
    make_dublincore("transfer", transfer.uuid)

    response = admin_client.post(
        reverse("api:transfer_reingest", kwargs={"target": "transfer"}),
        {"name": f"mytransfer-{transfer_uuid}", "uuid": str(transfer_uuid)},
    )
    assert response.status_code == 200

    # Verify the related models were deleted.
    assert Job.objects.count() == 0
    assert Task.objects.count() == 0
    assert SIP.objects.count() == 0
    assert RightsStatement.objects.count() == 0
    assert DublinCore.objects.count() == 0


@pytest.mark.django_db
def test_reingest_full(
    sip_path: pathlib.Path, admin_client: Client, dashboard_uuid: uuid.UUID
) -> None:
    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()

    shared_directory = sip_path.parent.parent

    # There are no existing Transfers initially.
    assert Transfer.objects.count() == 0

    with mock.patch("uuid.uuid4", return_value=transfer_uuid):
        response = admin_client.post(
            reverse("api:transfer_reingest", kwargs={"target": "transfer"}),
            {"name": sip_path.name, "uuid": sip_path.name[-36:]},
        )
    assert response.status_code == 200

    # Verify the Transfer in the payload contains the fake UUID.
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "message": "Approval successful.",
        "reingest_uuid": str(transfer_uuid),
    }

    # Verify a Transfer model was created.
    assert (
        Transfer.objects.filter(
            currentlocation=f"%sharedPath%watchedDirectories/activeTransfers/standardTransfer/mytransfer-{transfer_uuid}/",
            type=Transfer.ARCHIVEMATICA_AIP,
        ).count()
        == 1
    )

    # Verify the original content was moved to the active transfers directory.
    active_transfers_path = (
        shared_directory / "watchedDirectories" / "activeTransfers" / "standardTransfer"
    )
    assert [e.name for e in active_transfers_path.iterdir()] == [
        f"mytransfer-{transfer_uuid}"
    ]
    assert (
        active_transfers_path / f"mytransfer-{transfer_uuid}" / "myfile.txt"
    ).read_text() == "my file"


@pytest.mark.django_db
def test_reingest_full_fails_if_target_directory_already_exists(
    sip_path: pathlib.Path, admin_client: Client, dashboard_uuid: uuid.UUID
) -> None:
    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()

    shared_directory = sip_path.parent.parent

    # Create a directory with the same transfer name under active transfers.
    active_transfers_path = (
        shared_directory / "watchedDirectories" / "activeTransfers" / "standardTransfer"
    )
    (active_transfers_path / f"mytransfer-{transfer_uuid}").mkdir()

    with mock.patch("uuid.uuid4", return_value=transfer_uuid):
        response = admin_client.post(
            reverse("api:transfer_reingest", kwargs={"target": "transfer"}),
            {"name": sip_path.name, "uuid": sip_path.name[-36:]},
        )

    assert response.status_code == 400
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "error": True,
        "message": "There is already a transfer in standardTransfer with the same name.",
    }


@pytest.mark.django_db
def test_reingest_partial(
    sip_path: pathlib.Path, admin_client: Client, dashboard_uuid: uuid.UUID
) -> None:
    shared_directory = sip_path.parent.parent

    # A partial reingest reuses the SIP UUID in the response.
    reingest_uuid = sip_path.name[-36:]

    response = admin_client.post(
        reverse("api:ingest_reingest", kwargs={"target": "ingest"}),
        {"name": sip_path.name, "uuid": reingest_uuid},
    )
    assert response.status_code == 200

    # Verify the payload contains the reingest UUID.
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "message": "Approval successful.",
        "reingest_uuid": reingest_uuid,
    }

    # Verify the original content was moved to the reingest directory.
    reingests_path = shared_directory / "watchedDirectories" / "system" / "reingestAIP"
    assert [e.name for e in reingests_path.iterdir()] == [sip_path.name]
    assert (reingests_path / sip_path.name / "myfile.txt").read_text() == "my file"


@pytest.mark.django_db
def test_mark_hidden(admin_client, dashboard_uuid, transfer):
    # This endpoint considers the status attribute instead of jobs.
    transfer.status = PACKAGE_STATUS_COMPLETED_SUCCESSFULLY
    transfer.save()

    assert not transfer.hidden

    response = admin_client.delete(
        reverse(
            "api:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.uuid},
        )
    )
    assert response.status_code == 200

    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"removed": True}
    assert Transfer.objects.get(pk=transfer.uuid).hidden


@pytest.mark.django_db
def test_mark_completed_hidden(
    admin_client, dashboard_uuid, transfer, jobs_transfer_complete
):
    assert not transfer.hidden

    response = admin_client.delete(
        reverse("api:mark_completed_hidden", kwargs={"unit_type": "transfer"})
    )
    assert response.status_code == 200

    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"removed": [str(transfer.uuid)]}
    assert Transfer.objects.get(pk=transfer.uuid).hidden
