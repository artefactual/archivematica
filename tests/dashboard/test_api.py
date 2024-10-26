import datetime
import json
import uuid
from unittest import mock

import archivematicaFunctions
import pytest
import requests
from components import helpers
from components.api import views
from django.core.management import call_command
from django.urls import reverse
from django.utils.timezone import make_aware
from lxml import etree
from main.models import PACKAGE_STATUS_COMPLETED_SUCCESSFULLY
from main.models import SIP
from main.models import DashboardSetting
from main.models import DublinCore
from main.models import File
from main.models import Job
from main.models import LevelOfDescription
from main.models import MetadataAppliesToType
from main.models import RightsStatement
from main.models import SIPArrange
from main.models import Task
from main.models import Transfer
from processing import install_builtin_config


def load_fixture(fixtures):
    call_command("loaddata", *fixtures, **{"verbosity": 0})


@pytest.fixture
def dashboard_uuid(db):
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.fixture
def transfer(db):
    return Transfer.objects.create()


@pytest.fixture
def sip(db):
    return SIP.objects.create()


@pytest.fixture
def files(db, transfer, sip):
    return [File.objects.create(transfer=transfer, sip=sip)]


@pytest.fixture
def jobs_processing(db, transfer):
    return [
        Job.objects.create(
            jobuuid="ee3b39f6-2d57-431d-bdd6-6d38f50de371",
            microservicegroup="Examine contents",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T22:50:56Z",
            unittype="unitTransfer",
            jobtype="Examine contents?",
        ),
        Job.objects.create(
            jobuuid="3ed5ec03-ee7d-4ddc-bdfc-3b1e07170c2b",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T22:50:57Z",
            unittype="unitTransfer",
            jobtype="Load options to create SIPs",
        ),
        Job.objects.create(
            jobuuid="7bd82bc3-0694-4182-8f72-48fb13f0e8e8",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_EXECUTING_COMMANDS,
            createdtime="2016-10-04T22:50:57Z",
            unittype="unitTransfer",
            jobtype="Check transfer directory for objects",
        ),
    ]


@pytest.fixture
def jobs_user_input(db, transfer):
    return [
        Job.objects.create(
            jobuuid="b9390fbf-8c00-434c-ab4b-eb501ed2f490",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_AWAITING_DECISION,
            createdtime="2016-10-04T22:50:57Z",
            unittype="unitTransfer",
            jobtype="Create SIP(s)",
        )
    ]


@pytest.fixture
def jobs_failed(db, transfer):
    return [
        Job.objects.create(
            jobuuid="7d9ba893-08f1-4678-9fe9-294fdc729c55",
            microservicegroup="Failed transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-05T00:10:54Z",
            unittype="unitTransfer",
            jobtype="Move to the failed directory",
        )
    ]


@pytest.fixture
def jobs_rejected(db, transfer):
    return [
        Job.objects.create(
            jobuuid="b7902aae-ec5f-4290-a3d7-c47f844e8774",
            microservicegroup="Reject transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:48:27Z",
            unittype="unitTransfer",
            jobtype="Move to the rejected directory",
        )
    ]


@pytest.fixture
def jobs_transfer_complete(db, transfer):
    return [
        Job.objects.create(
            jobuuid="d51f6915-ae7f-4c23-8a02-fcec49941168",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:05:55Z",
            unittype="unitTransfer",
            jobtype="Create SIP from transfer objects",
        ),
        Job.objects.create(
            jobuuid="e7775bc2-613f-4fb7-abba-738dfa799c99",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:05:56Z",
            unittype="unitTransfer",
            jobtype="Move to SIP creation directory for completed transfers",
        ),
    ]


@pytest.fixture
def jobs_transfer_backlog(db, transfer):
    return [
        Job.objects.create(
            jobuuid="a39d74e4-c42e-404b-8c29-dde873ca48ad",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:40:12Z",
            unittype="unitTransfer",
            jobtype="Move transfer to backlog",
        ),
        Job.objects.create(
            jobuuid="bac0675d-44fe-4047-9713-f9ba9fe46eff",
            microservicegroup="Create SIP from Transfer",
            sipuuid=transfer.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:40:14Z",
            unittype="unitTransfer",
            jobtype="Create placement in backlog PREMIS events",
        ),
    ]


@pytest.fixture
def jobs_sip_complete(db, sip):
    return [
        Job.objects.create(
            jobuuid="299c727c-e72b-4070-ae0a-a78a5aa0cfd3",
            microservicegroup="Store AIP",
            sipuuid=sip.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:18:46Z",
            unittype="unitSIP",
            jobtype="Remove the processing directory",
        )
    ]


@pytest.fixture
def jobs_sip_complete_cleanup_last(db, sip):
    return [
        Job.objects.create(
            jobuuid="c3e2f1de-5cd2-4543-89de-e49a75a54dc4",
            microservicegroup="Store AIP",
            sipuuid=sip.uuid,
            currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
            createdtime="2016-10-04T23:18:47Z",
            unittype="unitSIP",
            jobtype="Clean up after storing AIP",
        )
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
    jobs_processing, jobs_transfer_complete, transfer, sip, files
):
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
    transfer, sip, jobs_processing, jobs_transfer_complete, jobs_sip_complete, files
):
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
    transfer,
    sip,
    jobs_processing,
    jobs_transfer_complete,
    jobs_sip_complete,
    jobs_sip_complete_cleanup_last,
    files,
):
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
    admin_client, dashboard_uuid, transfer, sip, jobs_transfer_complete, files
):
    resp = admin_client.get(
        reverse("api:transfer_status", args=[transfer.uuid]),
    )
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["status"] == "COMPLETE"
    assert payload["type"] == "transfer"
    assert payload["uuid"] == str(transfer.uuid)


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
def test_status_with_bogus_unit(admin_client, dashboard_uuid):
    """It should return a 400 error as the status cannot be determined."""
    bogus_transfer_id = "1642cbe0-b72d-432d-8fc9-94dad3a0e9dd"
    Transfer.objects.create(uuid=bogus_transfer_id)
    resp = admin_client.get(reverse("api:transfer_status", args=[bogus_transfer_id]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert (
        payload["message"]
        == f"Unable to determine the status of the unit {bogus_transfer_id}"
    )


@pytest.mark.django_db
def test_completed_units(transfer, sip, jobs_transfer_complete, files):
    completed = views._completed_units()
    assert completed == [str(transfer.uuid)]


@pytest.mark.django_db
def test_completed_units_with_bogus_unit(transfer, sip, jobs_transfer_complete, files):
    """Bogus units should be excluded and handled gracefully."""
    Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
    completed = views._completed_units()
    assert completed == [str(transfer.uuid)]


@pytest.mark.django_db
def test_completed_transfers(
    admin_client, dashboard_uuid, transfer, sip, jobs_transfer_complete, files
):
    resp = admin_client.get(reverse("api:completed_transfers"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed transfers successfully.",
        "results": [str(transfer.uuid)],
    }


@pytest.mark.django_db
def test_completed_transfers_with_bogus_transfer(
    admin_client, dashboard_uuid, transfer, sip, jobs_transfer_complete, files
):
    """Bogus transfers should be excluded and handled gracefully."""
    Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
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
    admin_client, dashboard_uuid, sip, jobs_sip_complete
):
    """Bogus ingests should be excluded and handled gracefully."""
    SIP.objects.create(uuid="de702ef5-dfac-430d-93f4-f0453b18ad2f")
    resp = admin_client.get(reverse("api:completed_ingests"))
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode("utf8"))
    assert payload == {
        "message": "Fetched completed ingests successfully.",
        "results": [str(sip.uuid)],
    }


@pytest.mark.django_db
def test_unit_jobs_with_bogus_unit_uuid(admin_client, dashboard_uuid):
    bogus_unit_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
    resp = admin_client.get(reverse("api:v2beta_jobs", args=[bogus_unit_uuid]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert payload["message"] == f"No jobs found for unit: {bogus_unit_uuid}"


@pytest.mark.django_db
def test_unit_jobs(admin_client, dashboard_uuid, transfer, jobs_transfer_backlog):
    # Add a task to an existing job
    task_uuid = uuid.uuid4()
    job_index = 1
    Task.objects.create(
        taskuuid=task_uuid,
        job=jobs_transfer_backlog[job_index],
        createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
        endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 10)),
        exitcode=0,
    )
    # each payload mapping has information about the job and its tasks
    expected = []
    for job in jobs_transfer_backlog:
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
    assert len(payload) == len(jobs_transfer_backlog)
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
    assert job["uuid"] == jobs_rejected[0].jobuuid


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
    assert job["uuid"] == jobs_rejected[0].jobuuid


@pytest.mark.django_db
def test_unit_jobs_with_detailed_task_output(
    admin_client, dashboard_uuid, transfer, jobs_rejected
):
    # Add a task to an existing job
    task_uuid = uuid.uuid4()
    Task.objects.create(
        taskuuid=task_uuid,
        job=jobs_rejected[0],
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
    bogus_task_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
    resp = admin_client.get(reverse("api:v2beta_task", args=[bogus_task_uuid]))
    assert resp.status_code == 400
    payload = json.loads(resp.content.decode("utf8"))
    assert payload["error"] is True
    assert payload["message"] == f"Task with UUID {bogus_task_uuid} does not exist"


@pytest.mark.django_db
def test_task(admin_client, dashboard_uuid, jobs_transfer_backlog):
    stored_job = jobs_transfer_backlog[1]
    # fixtures don't have any tasks
    task_uuid = uuid.uuid4()
    Task.objects.create(
        taskuuid=task_uuid,
        job=stored_job,
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


@pytest.mark.django_db
def test_get_levels_of_description(admin_client, dashboard_uuid):
    LevelOfDescription.objects.create(name="Item", sortorder=2)
    LevelOfDescription.objects.create(name="Collection", sortorder=0)
    LevelOfDescription.objects.create(name="Fonds", sortorder=1)
    expected = ["Collection", "Fonds", "Item"]

    resp = admin_client.get(reverse("api:get_levels_of_description"))
    payload = json.loads(resp.content.decode("utf8"))

    result = []
    for level_of_description in payload:
        name = next(iter(level_of_description.values()))
        result.append(name)

    assert result == expected


@pytest.fixture
def shared_dir(tmp_path, settings):
    shared_dir = tmp_path / "shared_dir"
    shared_dir.mkdir()

    (shared_dir / "sharedMicroServiceTasksConfigs" / "processingMCPConfigs").mkdir(
        parents=True
    )

    settings.SHARED_DIRECTORY = shared_dir.as_posix()
    install_builtin_config("default")
    install_builtin_config("automated")

    return shared_dir


def test_list_processing_configs(admin_client, dashboard_uuid, shared_dir):
    expected_names = sorted(["default", "automated"])
    response = admin_client.get(reverse("api:processing_configuration_list"))
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf8"))
    shared_dir = payload["processing_configurations"]
    assert len(shared_dir) == 2
    assert all(
        actual == expected for actual, expected in zip(shared_dir, expected_names)
    )


def test_get_existing_processing_config(admin_client, dashboard_uuid, shared_dir):
    response = admin_client.get(
        reverse("api:processing_configuration", args=["default"]),
        HTTP_ACCEPT="xml",
    )
    assert response.status_code == 200
    assert etree.fromstring(response.content).xpath(".//preconfiguredChoice")


def test_delete_and_regenerate(admin_client, dashboard_uuid, shared_dir):
    processing_configs = (
        shared_dir / "sharedMicroServiceTasksConfigs" / "processingMCPConfigs"
    )

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


def test_404_for_non_existent_config(admin_client, dashboard_uuid, shared_dir):
    response = admin_client.get(
        reverse("api:processing_configuration", args=["nonexistent"]),
        HTTP_ACCEPT="xml",
    )
    assert response.status_code == 404


def test_404_for_delete_non_existent_config(admin_client, dashboard_uuid, shared_dir):
    response = admin_client.delete(
        reverse("api:processing_configuration", args=["nonexistent"])
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_unit_status_multiple(
    jobs_failed,
    jobs_transfer_complete,
    jobs_rejected,
    jobs_user_input,
    jobs_transfer_backlog,
):
    """When the database contains 5 units of the following types:
    1. a failed transfer
    2. a completed transfer
    3. a rejected transfer
    4. a transfer awaiting user input
    5. a transfer in backlog
    then ``completed_units_efficient`` should return 3: the failed,
    the completed, and the in-backlog transfer.
    """
    failed_transfer = Transfer.objects.create()
    for job in jobs_failed:
        job.sipuuid = failed_transfer.uuid
        job.save()

    complete_transfer = Transfer.objects.create()
    for job in jobs_transfer_complete:
        job.sipuuid = complete_transfer.uuid
        job.save()

    rejected_transfer = Transfer.objects.create()
    for job in jobs_rejected:
        job.sipuuid = rejected_transfer.uuid
        job.save()

    awaiting_transfer = Transfer.objects.create()
    for job in jobs_user_input:
        job.sipuuid = awaiting_transfer.uuid
        job.save()

    backlog_transfer = Transfer.objects.create()
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
@mock.patch("components.api.views.authenticate_request", return_value=None)
@mock.patch(
    "components.filesystem_ajax.views._copy_from_transfer_sources",
    return_value=(None, ""),
)
def test_copy_metadata_files_api(_copy_from_transfer_sources, authenticate_request):
    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    SIP.objects.create(
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


@mock.patch(
    "components.filesystem_ajax.views.start_transfer",
    return_value={},
)
def test_start_transfer_api_decodes_paths(start_transfer_view, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
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


@mock.patch(
    "contrib.mcp.client.gearman.JOB_COMPLETE",
)
@mock.patch("contrib.mcp.client.GearmanClient")
def test_reingest_approve(gearman_client, job_complete, admin_client):
    gearman_client.return_value = mock.Mock(
        **{
            "submit_job.return_value": mock.Mock(
                state=job_complete,
                result=None,
            )
        }
    )
    helpers.set_setting("dashboard_uuid", "test-uuid")

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


def test_path_metadata_get(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    SIPArrange.objects.create(
        arrange_path=b"/arrange/testsip/", level_of_description="Folder"
    )

    response = admin_client.get(
        reverse("api:path_metadata"), {"path": "/arrange/testsip"}
    )
    assert response.status_code == 200

    payload = json.loads(response.content.decode("utf8"))
    assert payload["level_of_description"] == "Folder"


def test_path_metadata_raises_404_if_siparrange_does_not_exist(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.get(
        reverse("api:path_metadata"), {"path": "/arrange/testsip"}
    )
    assert response.status_code == 404


def test_path_metadata_post(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    SIPArrange.objects.create(
        arrange_path=b"/arrange/testsip/", level_of_description="Folder"
    )
    level_of_description = LevelOfDescription.objects.create(
        name="Collection", sortorder=0
    )
    expected = [
        {"arrange_path": b"/arrange/testsip/", "level_of_description": "Collection"}
    ]

    response = admin_client.post(
        reverse("api:path_metadata"),
        data={
            "path": "/arrange/testsip",
            "level_of_description": level_of_description.pk,
        },
    )
    assert response.status_code == 201

    payload = json.loads(response.content.decode("utf8"))
    assert payload["success"]

    # Verify the SIPArrange instance was updated as expected.
    assert (
        list(SIPArrange.objects.values("arrange_path", "level_of_description"))
        == expected
    )


def test_path_metadata_post_resets_level_of_description(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    SIPArrange.objects.create(
        arrange_path=b"/arrange/testsip/", level_of_description="Folder"
    )
    expected = [{"arrange_path": b"/arrange/testsip/", "level_of_description": ""}]

    response = admin_client.post(
        reverse("api:path_metadata"),
        data={"path": "/arrange/testsip"},
    )
    assert response.status_code == 201

    payload = json.loads(response.content.decode("utf8"))
    assert payload["success"]

    # Verify the level of description was reset.
    assert (
        list(SIPArrange.objects.values("arrange_path", "level_of_description"))
        == expected
    )


@pytest.mark.django_db
def test_unapproved_transfers(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Create a couple of jobs with one awaiting for decision, i.e. unapproved.
    approve_transfer_uuid = uuid.uuid4()
    Job.objects.create(
        jobtype="Approve standard transfer",
        currentstep=Job.STATUS_AWAITING_DECISION,
        directory="%sharedPath%watchedDirectories/activeTransfers/standardTransfer/test-2/",
        createdtime=make_aware(datetime.datetime(2023, 11, 14, 9, 20)),
        unittype="unitTransfer",
        sipuuid=approve_transfer_uuid,
    )
    Job.objects.create(
        jobtype="Store AIP",
        currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
        directory="%sharedPath%watchedDirectories/storeAIP/test-1/",
        createdtime=make_aware(datetime.datetime(2023, 11, 13, 0, 0)),
        unittype="unitSIP",
        sipuuid=uuid.UUID("520327f1-cd4e-47fe-9d8a-d9c02fded504"),
    )

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
                "uuid": str(approve_transfer_uuid),
            }
        ],
    }


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
@mock.patch("contrib.mcp.client.GearmanClient", side_effect=Exception())
def test_approve_transfer_failures(
    gearman_client, post_data, expected_error, admin_client
):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.post(reverse("api:approve_transfer"), post_data)

    assert response.status_code == 500
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"error": True, "message": expected_error}


@mock.patch("contrib.mcp.client.gearman.JOB_COMPLETE")
@mock.patch("contrib.mcp.client.GearmanClient")
def test_approve_transfer(gearman_client, job_complete, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

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
def test_waiting_for_user_input(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Create a couple of jobs with one awaiting for decision.
    approve_transfer_uuid = uuid.uuid4()
    Job.objects.create(
        jobtype="Approve standard transfer",
        currentstep=Job.STATUS_AWAITING_DECISION,
        directory="%sharedPath%watchedDirectories/activeTransfers/standardTransfer/test-2/",
        createdtime=make_aware(datetime.datetime(2023, 11, 14, 9, 20)),
        unittype="unitTransfer",
        sipuuid=approve_transfer_uuid,
    )
    Job.objects.create(
        jobtype="Store AIP",
        currentstep=Job.STATUS_COMPLETED_SUCCESSFULLY,
        directory="%sharedPath%watchedDirectories/storeAIP/test-1/",
        createdtime=make_aware(datetime.datetime(2023, 11, 13, 0, 0)),
        unittype="unitSIP",
        sipuuid=uuid.uuid4(),
    )

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
                "sip_uuid": str(approve_transfer_uuid),
            }
        ],
    }


def test_reingest_fails_with_missing_parameters(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.post(
        reverse("api:transfer_reingest", kwargs={"target": "transfer"}), {}
    )

    assert response.status_code == 400
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"error": True, "message": '"name" and "uuid" are required.'}


@pytest.fixture
def sip_path(tmp_path):
    shared_dir = tmp_path / "dir"
    shared_dir.mkdir()

    (shared_dir / "watchedDirectories" / "activeTransfers" / "standardTransfer").mkdir(
        parents=True
    )
    (shared_dir / "watchedDirectories" / "system" / "reingestAIP").mkdir(parents=True)

    tmp_dir = shared_dir / "tmp"
    tmp_dir.mkdir()

    sip_dir = tmp_dir / f"mytransfer-{uuid.uuid4()}"
    sip_dir.mkdir()
    (sip_dir / "myfile.txt").write_text("my file")

    return sip_dir


@pytest.mark.django_db
def test_reingest_deletes_existing_models_related_to_sip(
    sip_path, settings, admin_client
):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    transfer_uuid = sip_path.name[-36:]
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

    # Create a Transfer and related models.
    transfer = Transfer.objects.create(uuid=transfer_uuid)
    job = Job.objects.create(
        sipuuid=transfer.uuid,
        createdtime=make_aware(datetime.datetime(2023, 11, 15, 8, 30)),
    )
    Task.objects.create(
        job=job,
        createdtime=make_aware(datetime.datetime(2023, 11, 15, 8, 30)),
    )
    SIP.objects.create(uuid=transfer.uuid)
    metadata_applies_to_type = MetadataAppliesToType.objects.create()
    RightsStatement.objects.create(
        metadataappliestoidentifier=transfer.uuid,
        metadataappliestotype=metadata_applies_to_type,
    )
    DublinCore.objects.create(
        metadataappliestoidentifier=transfer.uuid,
        metadataappliestotype=metadata_applies_to_type,
    )

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
def test_reingest_full(sip_path, settings, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

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
            currentlocation=f"%sharedPath%/watchedDirectories/activeTransfers/standardTransfer/mytransfer-{transfer_uuid}/",
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
    sip_path, settings, admin_client
):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

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
def test_reingest_partial(sip_path, settings, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

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
@mock.patch("requests.get")
def test_fetch_levels_of_description_from_atom(get, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Set up the AtoM settings used on the Administration tab.
    DashboardSetting.objects.create(
        name="upload-qubit_v0.0",
        value=str(
            {
                "url": "http://example.com",
                "email": "demo@example.com",
                "password": "password",
            }
        ),
    )

    # Simulate interaction with AtoM.
    lods = ["Series", "Subseries", "File"]
    get.side_effect = [
        mock.Mock(
            **{
                "status_code": 200,
                "json.return_value": [{"name": lod} for lod in lods],
            },
            spec=requests.Response,
        )
    ]

    # Add existing LODs before calling the endpoint.
    LevelOfDescription.objects.create(name="One existing", sortorder=1)
    LevelOfDescription.objects.create(name="Another existing", sortorder=1)

    response = admin_client.get(reverse("api:fetch_atom_lods"))
    assert response.status_code == 200

    # Verify the initial LODS were deleted and we only have the retrieved ones.
    result = []
    for lod in json.loads(response.content.decode("utf8")):
        # LODs are represented as [{"8263fd14-2488-49f7-ac9d-fcfd02b524f0": "Series"}, ...]
        name = list(lod.values())[0]
        result.append(name)
    assert result == lods
    assert set(LevelOfDescription.objects.values_list("name")) == {
        (lod,) for lod in lods
    }


@pytest.mark.django_db
@mock.patch(
    "requests.get", side_effect=[mock.Mock(status_code=503, spec=requests.Response)]
)
def test_fetch_levels_of_description_from_atom_communication_failure(get, admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Set up the AtoM settings used on the Administration tab.
    DashboardSetting.objects.create(
        name="upload-qubit_v0.0",
        value=str(
            {
                "url": "http://example.com",
                "email": "demo@example.com",
                "password": "password",
            }
        ),
    )

    response = admin_client.get(reverse("api:fetch_atom_lods"))

    assert response.status_code == 500
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "success": False,
        "error": "Unable to fetch levels of description from AtoM!",
    }


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
