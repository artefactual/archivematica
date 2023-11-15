import datetime
import json
import os
import tempfile
import uuid

import archivematicaFunctions
import pytest
import requests
from components import helpers
from components.api import views
from django.core.management import call_command
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils.timezone import make_aware
from lxml import etree
from main.models import DashboardSetting
from main.models import DublinCore
from main.models import Job
from main.models import LevelOfDescription
from main.models import MetadataAppliesToType
from main.models import RightsStatement
from main.models import SIP
from main.models import SIPArrange
from main.models import Task
from main.models import Transfer
from processing import install_builtin_config


def load_fixture(fixtures):
    call_command("loaddata", *fixtures, **{"verbosity": 0})


def e2e(fn):
    """Use this decorator when your test uses the HTTP client."""

    def _wrapper(self, *args):
        load_fixture(["test_user"])
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")
        return fn(self, *args)

    return _wrapper


class TestAPI(TestCase):
    """Test API endpoints."""

    fixtures = ["transfer", "sip"]

    def _test_api_error(self, response, message=None, status_code=None):
        payload = json.loads(response.content.decode("utf8"))
        assert payload["error"] is True
        if message is not None:
            assert payload["message"] == message
        else:
            assert "message" in payload
        if status_code is not None:
            assert response.status_code == status_code

    def test_get_unit_status_processing(self):
        """It should return PROCESSING."""
        # Setup fixtures
        load_fixture(["jobs-processing"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "PROCESSING"
        assert len(completed) == 0

    def test_get_unit_status_user_input(self):
        """It should return USER_INPUT."""
        # Setup fixtures
        load_fixture(["jobs-processing", "jobs-user-input"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "USER_INPUT"
        assert len(completed) == 0

    def test_get_unit_status_failed(self):
        """It should return FAILED."""
        # Setup fixtures
        load_fixture(["jobs-processing", "jobs-failed"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "FAILED"
        assert len(completed) == 1

    def test_get_unit_status_rejected(self):
        """It should return REJECTED."""
        # Setup fixtures
        load_fixture(["jobs-processing", "jobs-rejected"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "REJECTED"
        assert len(completed) == 0

    def test_get_unit_status_completed_transfer(self):
        """It should return COMPLETE and the new SIP UUID."""
        # Setup fixtures
        load_fixture(["jobs-processing", "jobs-transfer-complete", "files"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 3
        assert "microservice" in status
        assert status["status"] == "COMPLETE"
        assert status["sip_uuid"] == "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        assert len(completed) == 1

    def test_get_unit_status_backlog(self):
        """It should return COMPLETE and in BACKLOG."""
        # Setup fixtures
        load_fixture(["jobs-processing", "jobs-transfer-backlog"])
        # Test
        status = views.get_unit_status(
            "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e", "unitTransfer"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 3
        assert "microservice" in status
        assert status["status"] == "COMPLETE"
        assert status["sip_uuid"] == "BACKLOG"
        assert len(completed) == 1

    def test_get_unit_status_completed_sip(self):
        """It should return COMPLETE."""
        # Setup fixtures
        load_fixture(
            ["jobs-processing", "jobs-transfer-complete", "jobs-sip-complete", "files"]
        )
        # Test
        status = views.get_unit_status(
            "4060ee97-9c3f-4822-afaf-ebdf838284c3", "unitSIP"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "COMPLETE"
        assert len(completed) == 1

    def test_get_unit_status_completed_sip_issue_262_workaround(self):
        """Test get unit status for a completed SIP when the job with the latest
        created time is not the last in the microservice chain
        (i.e, job with jobtype 'Remove the processing directory' is not the one with
        latest created time)
        It should return COMPLETE."""
        # Setup fixtures
        load_fixture(
            [
                "jobs-processing",
                "jobs-transfer-complete",
                "jobs-sip-complete-clean-up-last",
                "files",
            ]
        )
        # Test
        status = views.get_unit_status(
            "4060ee97-9c3f-4822-afaf-ebdf838284c3", "unitSIP"
        )
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        # Verify
        assert len(status) == 2
        assert "microservice" in status
        assert status["status"] == "COMPLETE"
        assert len(completed) == 1

    @e2e
    def test_status(self):
        load_fixture(["jobs-transfer-complete", "files"])
        resp = self.client.get(
            reverse(
                "api:transfer_status", args=["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"]
            ),
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload["status"] == "COMPLETE"
        assert payload["type"] == "transfer"
        assert payload["uuid"] == "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"

    @e2e
    def test_status_with_bogus_unit(self):
        """It should return a 400 error as the status cannot be determined."""
        bogus_transfer_id = "1642cbe0-b72d-432d-8fc9-94dad3a0e9dd"
        Transfer.objects.create(uuid=bogus_transfer_id)
        resp = self.client.get(reverse("api:transfer_status", args=[bogus_transfer_id]))
        self._test_api_error(
            resp,
            status_code=400,
            message=(
                "Unable to determine the status of the unit {}".format(
                    bogus_transfer_id
                )
            ),
        )

    def test_completed_units(self):
        load_fixture(["jobs-transfer-complete", "files"])
        completed = views._completed_units()
        assert completed == ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"]

    def test_completed_units_with_bogus_unit(self):
        """Bogus units should be excluded and handled gracefully."""
        load_fixture(["jobs-transfer-complete", "files"])
        Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
        try:
            completed = views._completed_units()
        except Exception as err:
            self.fail("views._completed_units raised unexpected exception", err)
        assert completed == ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"]

    @e2e
    def test_completed_transfers(self):
        load_fixture(["jobs-transfer-complete", "files"])
        resp = self.client.get(reverse("api:completed_transfers"))
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed transfers successfully.",
            "results": ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"],
        }

    @e2e
    def test_completed_transfers_with_bogus_transfer(self):
        """Bogus transfers should be excluded and handled gracefully."""
        load_fixture(["jobs-transfer-complete", "files"])
        Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
        resp = self.client.get(reverse("api:completed_transfers"))
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed transfers successfully.",
            "results": ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"],
        }

    @e2e
    def test_completed_ingests(self):
        load_fixture(["jobs-sip-complete"])
        resp = self.client.get(reverse("api:completed_ingests"))
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed ingests successfully.",
            "results": ["4060ee97-9c3f-4822-afaf-ebdf838284c3"],
        }

    @e2e
    def test_completed_ingests_with_bogus_sip(self):
        """Bogus ingests should be excluded and handled gracefully."""
        load_fixture(["jobs-sip-complete"])
        SIP.objects.create(uuid="de702ef5-dfac-430d-93f4-f0453b18ad2f")
        resp = self.client.get(reverse("api:completed_ingests"))
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed ingests successfully.",
            "results": ["4060ee97-9c3f-4822-afaf-ebdf838284c3"],
        }

    @e2e
    def test_unit_jobs_with_bogus_unit_uuid(self):
        bogus_unit_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
        resp = self.client.get(reverse("api:v2beta_jobs", args=[bogus_unit_uuid]))
        self._test_api_error(
            resp,
            status_code=400,
            message=(f"No jobs found for unit: {bogus_unit_uuid}"),
        )

    @e2e
    def test_unit_jobs(self):
        load_fixture(["jobs-transfer-backlog"])
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        # fixtures don't have any tasks
        Task.objects.create(
            taskuuid="12345678-1234-1234-1234-123456789012",
            job=Job.objects.get(jobuuid="d2f99030-26b9-4746-b100-856779624934"),
            createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
            starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0)),
            endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 10)),
            exitcode=0,
        )
        resp = self.client.get(reverse("api:v2beta_jobs", args=[sip_uuid]))
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        # payload contains a mapping for each job
        assert len(payload) == 5
        expected_job_uuids = [
            "624581dc-ec01-4195-9da3-db0ab0ad1cc3",
            "a39d74e4-c42e-404b-8c29-dde873ca48ad",
            "bac0675d-44fe-4047-9713-f9ba9fe46eff",
            "c763fa11-0e36-4b93-a8c8-6f008b74a96a",
            "d2f99030-26b9-4746-b100-856779624934",
        ]
        # sort the payload results by job uuid
        sorted_payload = sorted(payload, key=lambda job: job["uuid"])
        assert [job["uuid"] for job in sorted_payload] == expected_job_uuids
        # each payload mapping has information about the job and its tasks
        job = sorted_payload[4]
        assert job["uuid"] == "d2f99030-26b9-4746-b100-856779624934"
        assert job["name"] == "Check transfer directory for objects"
        assert job["status"] == "COMPLETE"
        assert job["microservice"] == "Create SIP from Transfer"
        assert job["link_uuid"] is None
        assert job["tasks"] == [
            {"uuid": "12345678-1234-1234-1234-123456789012", "exit_code": 0}
        ]

    @e2e
    def test_unit_jobs_searching_for_microservice(self):
        load_fixture(["jobs-rejected"])
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        resp = self.client.get(
            reverse("api:v2beta_jobs", args=[sip_uuid]),
            {"microservice": "Reject transfer"},
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "b7902aae-ec5f-4290-a3d7-c47f844e8774"
        assert job["name"] == "Move to the rejected directory"
        assert job["status"] == "COMPLETE"
        assert job["microservice"] == "Reject transfer"
        assert job["link_uuid"] is None
        assert job["tasks"] == []
        # Test that microservice search also works with a "Microservice:" prefix
        resp = self.client.get(
            reverse("api:v2beta_jobs", args=[sip_uuid]),
            {"microservice": "Microservice: Reject transfer"},
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "b7902aae-ec5f-4290-a3d7-c47f844e8774"

    @e2e
    def test_unit_jobs_searching_for_chain_link(self):
        load_fixture(["jobs-rejected"])
        # add chain links to the fixture jobs
        job = Job.objects.get(jobuuid="59ace00b-4830-4314-a7d9-38fdbef64896")
        job.microservicechainlink = "0b8f1929-5beb-4998-a2d5-40e4873fa887"
        job.save()
        job = Job.objects.get(jobuuid="b7902aae-ec5f-4290-a3d7-c47f844e8774")
        job.microservicechainlink = "2208efc0-ba99-4b36-bb8d-99330fcc25da"
        job.save()
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        resp = self.client.get(
            reverse("api:v2beta_jobs", args=[sip_uuid]),
            {"link_uuid": "0b8f1929-5beb-4998-a2d5-40e4873fa887"},
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "59ace00b-4830-4314-a7d9-38fdbef64896"
        assert job["name"] == "Create SIP(s)"
        assert job["status"] == "COMPLETE"
        assert job["microservice"] == "Create SIP from Transfer"
        assert job["link_uuid"] == "0b8f1929-5beb-4998-a2d5-40e4873fa887"
        assert job["tasks"] == []

    @e2e
    def test_unit_jobs_searching_for_name(self):
        load_fixture(["jobs-rejected"])
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        resp = self.client.get(
            reverse("api:v2beta_jobs", args=[sip_uuid]),
            {"name": "Move to the rejected directory"},
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "b7902aae-ec5f-4290-a3d7-c47f844e8774"
        assert job["name"] == "Move to the rejected directory"
        assert job["status"] == "COMPLETE"
        assert job["microservice"] == "Reject transfer"
        assert job["link_uuid"] is None
        assert job["tasks"] == []
        # Test that name search also works with a "Job:" prefix
        resp = self.client.get(
            reverse("api:v2beta_jobs", args=[sip_uuid]),
            {"name": "Job: Move to the rejected directory"},
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "b7902aae-ec5f-4290-a3d7-c47f844e8774"

    @e2e
    def test_task_with_bogus_task_uuid(self):
        bogus_task_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
        resp = self.client.get(reverse("api:v2beta_task", args=[bogus_task_uuid]))
        self._test_api_error(
            resp,
            status_code=400,
            message=(f"Task with UUID {bogus_task_uuid} does not exist"),
        )

    @e2e
    def test_task(self):
        load_fixture(["jobs-transfer-backlog"])
        # fixtures don't have any tasks
        Task.objects.create(
            taskuuid="12345678-1234-1234-1234-123456789012",
            job=Job.objects.get(jobuuid="d2f99030-26b9-4746-b100-856779624934"),
            createdtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 0)),
            starttime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 0)),
            endtime=make_aware(datetime.datetime(2019, 6, 18, 0, 0, 5)),
            exitcode=0,
        )
        resp = self.client.get(
            reverse("api:v2beta_task", args=["12345678-1234-1234-1234-123456789012"])
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        # payload is a mapping of task attributes
        assert payload["uuid"] == "12345678-1234-1234-1234-123456789012"
        assert payload["exit_code"] == 0
        assert payload["file_uuid"] is None
        assert payload["file_name"] == ""
        assert payload["time_created"] == "2019-06-18T00:00:00"
        assert payload["time_started"] == "2019-06-18T00:00:00"
        assert payload["time_ended"] == "2019-06-18T00:00:05"
        assert payload["duration"] == 5

    @e2e
    def test_get_levels_of_description(self):
        LevelOfDescription.objects.create(name="Item", sortorder=2)
        LevelOfDescription.objects.create(name="Collection", sortorder=0)
        LevelOfDescription.objects.create(name="Fonds", sortorder=1)
        expected = ["Collection", "Fonds", "Item"]

        resp = self.client.get(reverse("api:get_levels_of_description"))
        payload = json.loads(resp.content.decode("utf8"))

        result = []
        for level_of_description in payload:
            name = next(iter(level_of_description.values()))
            result.append(name)

        assert result == expected


class TestProcessingConfigurationAPI(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")
        self.populate_shared_dir()

    def populate_shared_dir(self):
        self.shared_dir = tempfile.gettempdir()
        self.config_path = os.path.join(
            self.shared_dir,
            "sharedMicroServiceTasksConfigs/processingMCPConfigs/",
        )
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
        with self.settings(SHARED_DIRECTORY=self.shared_dir):
            install_builtin_config("default")
            install_builtin_config("automated")

    def test_list_processing_configs(self):
        with self.settings(SHARED_DIRECTORY=self.shared_dir):
            response = self.client.get(reverse("api:processing_configuration_list"))
            assert response.status_code == 200
            payload = json.loads(response.content.decode("utf8"))
            processing_configs = payload["processing_configurations"]
            assert len(processing_configs) == 2
            expected_names = sorted(["default", "automated"])
            assert all(
                [
                    actual == expected
                    for actual, expected in zip(processing_configs, expected_names)
                ]
            )

    def test_get_existing_processing_config(self):
        with self.settings(SHARED_DIRECTORY=self.shared_dir):
            response = self.client.get(
                reverse("api:processing_configuration", args=["default"]),
                HTTP_ACCEPT="xml",
            )
            assert response.status_code == 200
            assert etree.fromstring(response.content).xpath(".//preconfiguredChoice")

    def test_delete_and_regenerate(self):
        with self.settings(SHARED_DIRECTORY=self.shared_dir):
            response = self.client.delete(
                reverse("api:processing_configuration", args=["default"])
            )
            assert response.status_code == 200
            assert not os.path.exists(
                os.path.join(self.config_path, "defaultProcessingMCP.xml")
            )

            response = self.client.get(
                reverse("api:processing_configuration", args=["default"]),
                HTTP_ACCEPT="xml",
            )
            assert response.status_code == 200
            assert etree.fromstring(response.content).xpath(".//preconfiguredChoice")
            assert os.path.exists(
                os.path.join(self.config_path, "defaultProcessingMCP.xml")
            )

    def test_404_for_non_existent_config(self):
        response = self.client.get(
            reverse("api:processing_configuration", args=["nonexistent"]),
            HTTP_ACCEPT="xml",
        )
        assert response.status_code == 404

    def test_404_for_delete_non_existent_config(self):
        response = self.client.delete(
            reverse("api:processing_configuration", args=["nonexistent"])
        )
        assert response.status_code == 404


class TestAPI2(TestCase):
    """Test API endpoints."""

    fixtures = ["units", "jobs-various"]

    def test_get_unit_status_multiple(self):
        """When the database contains 5 units of the following types:
        1. a failed transfer b949773d-7cf7-4c1e-aea5-ccbf65b70ccd
        2. a completed transfer 85216028-1150-4321-abb3-31ea570a341b
        3. a rejected transfer c9cce131-7bd9-41c8-82ab-483190961ae2
        4. a transfer awaiting user input 37a07d96-6fc0-4002-b269-471a58783805
        5. a transfer in backlog 5d0ab97f-a45b-4e0f-9cb6-90ee3a404549
        then ``completed_units_efficient`` should return 3: the failed,
        the completed, and the in-backlog transfer.
        """
        completed = helpers.completed_units_efficient(
            unit_type="transfer", include_failed=True
        )
        assert len(completed) == 3
        assert "85216028-1150-4321-abb3-31ea570a341b" in completed
        assert "5d0ab97f-a45b-4e0f-9cb6-90ee3a404549" in completed
        assert "b949773d-7cf7-4c1e-aea5-ccbf65b70ccd" in completed


@pytest.mark.django_db
def test_copy_metadata_files_api(mocker):
    # Mock authentication helper
    mocker.patch("components.api.views.authenticate_request", return_value=None)

    # Mock helper that actually copies files from the transfer source locations
    mocker.patch(
        "components.filesystem_ajax.views._copy_from_transfer_sources",
        return_value=(None, ""),
    )

    # Create a SIP
    sip_uuid = str(uuid.uuid4())
    SIP.objects.create(
        uuid=sip_uuid,
        currentpath=f"%sharedPath%more/path/metadataReminder/mysip-{sip_uuid}/",
    )

    # Call the endpoint with a mocked request
    request = mocker.Mock(
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


def test_start_transfer_api_decodes_paths(mocker, admin_client):
    start_transfer_view = mocker.patch(
        "components.filesystem_ajax.views.start_transfer",
        return_value={},
    )
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


def test_reingest_approve(mocker, admin_client):
    mocker.patch("contrib.mcp.client.pickle")
    job_complete = mocker.patch(
        "contrib.mcp.client.gearman.JOB_COMPLETE",
    )
    mocker.patch(
        "gearman.GearmanClient",
        return_value=mocker.Mock(
            **{"submit_job.return_value": mocker.Mock(state=job_complete)}
        ),
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
def test_approve_transfer_failures(post_data, expected_error, admin_client, mocker):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Simulate an unhandled error when calling Gearman.
    mocker.patch("contrib.mcp.client.MCPClient", side_effect=Exception())

    response = admin_client.post(reverse("api:approve_transfer"), post_data)

    assert response.status_code == 500
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {"error": True, "message": expected_error}


def test_approve_transfer(admin_client, mocker):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Simulate a dashboard <-> Gearman <-> MCPServer interaction.
    # The MCPServer approveTransferByPath RPC method returns a UUID.
    transfer_uuid = uuid.uuid4()
    mocker.patch("contrib.mcp.client.pickle.loads", side_effect=[transfer_uuid])
    job_complete = mocker.patch(
        "contrib.mcp.client.gearman.JOB_COMPLETE",
    )
    mocker.patch(
        "gearman.GearmanClient",
        return_value=mocker.Mock(
            **{"submit_job.return_value": mocker.Mock(state=job_complete)}
        ),
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
def test_reingest_full(sip_path, settings, admin_client, mocker):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()
    mocker.patch("uuid.uuid4", return_value=transfer_uuid)

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

    # There are no existing Transfers initially.
    assert Transfer.objects.count() == 0

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
    sip_path, settings, admin_client, mocker
):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    # Fake UUID generation from the endpoint for a new Transfer.
    transfer_uuid = uuid.uuid4()
    mocker.patch("uuid.uuid4", return_value=transfer_uuid)

    # Set the SHARED_DIRECTORY setting based on the sip_path fixture.
    shared_directory = sip_path.parent.parent
    settings.SHARED_DIRECTORY = shared_directory.as_posix()

    # Create a directory with the same transfer name under active transfers.
    active_transfers_path = (
        shared_directory / "watchedDirectories" / "activeTransfers" / "standardTransfer"
    )
    (active_transfers_path / f"mytransfer-{transfer_uuid}").mkdir()

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
def test_fetch_levels_of_description_from_atom(admin_client, mocker):
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
    mocker.patch(
        "requests.get",
        side_effect=[
            mocker.Mock(
                **{
                    "status_code": 200,
                    "json.return_value": [{"name": lod} for lod in lods],
                },
                spec=requests.Response,
            )
        ],
    )

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
def test_fetch_levels_of_description_from_atom_communication_failure(
    admin_client, mocker
):
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

    # Simulate failing interaction with AtoM.
    mocker.patch(
        "requests.get",
        side_effect=[mocker.Mock(status_code=503, spec=requests.Response)],
    )

    response = admin_client.get(reverse("api:fetch_atom_lods"))

    assert response.status_code == 500
    payload = json.loads(response.content.decode("utf8"))
    assert payload == {
        "success": False,
        "error": "Unable to fetch levels of description from AtoM!",
    }
