# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import json
import os
import tempfile
import uuid

from django.core.management import call_command
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils.timezone import make_aware
from lxml import etree
import pytest

from archivematicaFunctions import b64encode_string
from components.api import views
from components import helpers
from main.models import Job, SIP, Task, Transfer
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
        load_fixture(["jobs-processing", "jobs-transfer-complete", "jobs-sip-complete"])
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
        load_fixture(["jobs-transfer-complete"])
        resp = self.client.get(
            "/api/transfer/status/3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
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
        resp = self.client.get("/api/transfer/status/{}".format(bogus_transfer_id))
        self._test_api_error(
            resp,
            status_code=400,
            message=(
                "Unable to determine the status of the unit {}".format(
                    bogus_transfer_id
                )
            ),
        )

    def test__completed_units(self):
        load_fixture(["jobs-transfer-complete"])
        completed = views._completed_units()
        assert completed == ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"]

    def test__completed_units_with_bogus_unit(self):
        """Bogus units should be excluded and handled gracefully."""
        load_fixture(["jobs-transfer-complete"])
        Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
        try:
            completed = views._completed_units()
        except Exception as err:
            self.fail("views._completed_units raised unexpected exception", err)
        assert completed == ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"]

    @e2e
    def test_completed_transfers(self):
        load_fixture(["jobs-transfer-complete"])
        resp = self.client.get("/api/transfer/completed")
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed transfers successfully.",
            "results": ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"],
        }

    @e2e
    def test_completed_transfers_with_bogus_transfer(self):
        """Bogus transfers should be excluded and handled gracefully."""
        load_fixture(["jobs-transfer-complete"])
        Transfer.objects.create(uuid="1642cbe0-b72d-432d-8fc9-94dad3a0e9dd")
        resp = self.client.get("/api/transfer/completed")
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed transfers successfully.",
            "results": ["3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"],
        }

    @e2e
    def test_completed_ingests(self):
        load_fixture(["jobs-sip-complete"])
        resp = self.client.get("/api/ingest/completed")
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
        resp = self.client.get("/api/ingest/completed")
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert payload == {
            "message": "Fetched completed ingests successfully.",
            "results": ["4060ee97-9c3f-4822-afaf-ebdf838284c3"],
        }

    @e2e
    def test_unit_jobs_with_bogus_unit_uuid(self):
        bogus_unit_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
        resp = self.client.get("/api/v2beta/jobs/{}".format(bogus_unit_uuid))
        self._test_api_error(
            resp,
            status_code=400,
            message=("No jobs found for unit: {}".format(bogus_unit_uuid)),
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
        resp = self.client.get("/api/v2beta/jobs/{}".format(sip_uuid))
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
            "/api/v2beta/jobs/{}?microservice={}".format(sip_uuid, "Reject transfer")
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
            "/api/v2beta/jobs/{}?microservice={}".format(
                sip_uuid, "Microservice: Reject transfer"
            )
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
        job.microservicechainlink = "11111111-1111-1111-1111-111111111111"
        job.save()
        job = Job.objects.get(jobuuid="b7902aae-ec5f-4290-a3d7-c47f844e8774")
        job.microservicechainlink = "22222222-2222-2222-2222-222222222222"
        job.save()
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        resp = self.client.get(
            "/api/v2beta/jobs/{}?link_uuid={}".format(
                sip_uuid, "11111111-1111-1111-1111-111111111111"
            )
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "59ace00b-4830-4314-a7d9-38fdbef64896"
        assert job["name"] == "Create SIP(s)"
        assert job["status"] == "COMPLETE"
        assert job["microservice"] == "Create SIP from Transfer"
        assert job["link_uuid"] == "11111111-1111-1111-1111-111111111111"
        assert job["tasks"] == []

    @e2e
    def test_unit_jobs_searching_for_name(self):
        load_fixture(["jobs-rejected"])
        sip_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        resp = self.client.get(
            "/api/v2beta/jobs/{}?name={}".format(
                sip_uuid, "Move to the rejected directory"
            )
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
            "/api/v2beta/jobs/{}?name={}".format(
                sip_uuid, "Job: Move to the rejected directory"
            )
        )
        assert resp.status_code == 200
        payload = json.loads(resp.content.decode("utf8"))
        assert len(payload) == 1
        job = payload[0]
        assert job["uuid"] == "b7902aae-ec5f-4290-a3d7-c47f844e8774"

    @e2e
    def test_task_with_bogus_task_uuid(self):
        bogus_task_uuid = "00000000-dfac-430d-93f4-f0453b18ad2f"
        resp = self.client.get("/api/v2beta/task/{}".format(bogus_task_uuid))
        self._test_api_error(
            resp,
            status_code=400,
            message=("Task with UUID {} does not exist".format(bogus_task_uuid)),
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
        resp = self.client.get("/api/v2beta/task/12345678-1234-1234-1234-123456789012")
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
        currentpath="%sharedPath%more/path/metadataReminder/mysip-{}/".format(sip_uuid),
    )

    # Call the endpoint with a mocked request
    request = mocker.Mock(
        **{
            "POST.get.return_value": sip_uuid,
            "POST.getlist.return_value": [b64encode_string("locationuuid:/some/path")],
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
