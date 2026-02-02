import json
import logging
import pathlib
import uuid
from unittest import mock

import pytest
from agentarchives.archivesspace import ArchivesSpaceError
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from archivematica.dashboard.components.ingest.pair_matcher import (
    ingest_upload_atk_get_dip_object_paths,
)
from archivematica.dashboard.components.ingest.views_as import get_as_system_client
from archivematica.dashboard.main import models
from archivematica.dashboard.main.models import Access
from archivematica.dashboard.main.models import ArchivesSpaceDIPObjectResourcePairing
from archivematica.dashboard.main.models import DashboardSetting

TEST_USER_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "test_user.json"
SIP_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "sip.json"
JOBS_SIP_COMPLETE_FIXTURE = (
    pathlib.Path(__file__).parent / "fixtures" / "jobs-sip-complete.json"
)


class TestIngest(TestCase):
    fixtures = [TEST_USER_FIXTURE, SIP_FIXTURE, JOBS_SIP_COMPLETE_FIXTURE]

    @pytest.fixture(autouse=True)
    def dashboard_uuid(self, dashboard_uuid):
        return dashboard_uuid

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")

    @mock.patch("agentarchives.archivesspace.ArchivesSpaceClient._login")
    def test_get_as_system_client(self, __):
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {
                "base_url": "http://foobar.tld",
                "user": "user",
                "passwd": "12345",
                "repository": "5",
            },
        )
        client = get_as_system_client()
        assert client.base_url == "http://foobar.tld"
        assert client.user == "user"
        assert client.passwd == "12345"
        assert client.repository == "/repositories/5"

        # It raises error when "base_url" is missing.
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {"user": "user", "passwd": "12345", "repository": "5"},
        )
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()

        # It raises error when "base_url" is empty.
        DashboardSetting.objects.set_dict(
            "upload-archivesspace_v0.0",
            {"base_url": "", "user": "user", "passwd": "12345", "repository": "5"},
        )
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()

    def test_normalization_event_detail_view(self):
        """Test the 'Manual normalization event detail' view of a SIP"""
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        url = reverse("ingest:ingest_metadata_event_detail", args=[sip_uuid])
        response = self.client.get(url)
        assert response.status_code == 200
        title = "".join(
            ["<h1>Normalization Event Detail<br />", "<small>test</small>", "</h1>"]
        )
        assert title in response.content.decode("utf8")

    def test_add_metadata_files_view(self):
        """Test the 'Add metadata files' view of a SIP"""
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        url = reverse("ingest:ingest_metadata_add_files", args=[sip_uuid])
        response = self.client.get(url)
        assert response.status_code == 200
        title = "\n    ".join(
            ["<h1>", "  Add metadata files<br />", "  <small>test</small>", "</h1>"]
        )
        assert title in response.content.decode("utf8")

    @mock.patch(
        "archivematica.dashboard.components.ingest.views.storage_service.get_location"
    )
    def test_add_metadata_files_view_uses_unnamed_when_sip_has_no_jobs(
        self, mocked_get_location
    ):
        mocked_get_location.return_value = []
        sip_uuid = str(uuid.uuid4())
        url = reverse("ingest:ingest_metadata_add_files", args=[sip_uuid])

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.context["name"] == "(Unnamed)"
        assert "(Unnamed)" in response.content.decode("utf8")
        mocked_get_location.assert_called_once_with(purpose="TS")

    @mock.patch(
        "archivematica.dashboard.components.ingest.views.storage_service.get_location"
    )
    def test_add_metadata_files_view_includes_editor_payload_for_valid_source_directories(
        self, mocked_get_location
    ):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        mocked_get_location.return_value = [
            {"uuid": "source-a", "path": "/var/archivematica/source-a"},
            {"uuid": "source-b", "path": "/var/archivematica/source-b"},
        ]

        response = self.client.get(
            reverse("ingest:ingest_metadata_add_files", args=[sip_uuid]),
        )

        assert response.status_code == 200
        assert response.context["editor_payload"] == {
            "sipUUID": sip_uuid,
            "sourceDirectories": {
                "source-a": "/var/archivematica/source-a",
                "source-b": "/var/archivematica/source-b",
            },
        }
        content = response.content.decode("utf8")
        assert '<div id="md-editor"></div>' in content
        assert 'id="md-editor-data"' in content

    @mock.patch(
        "archivematica.dashboard.components.ingest.views.storage_service.get_location"
    )
    def test_add_metadata_files_view_ignores_invalid_source_directory_entries(
        self, mocked_get_location
    ):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        mocked_get_location.return_value = [
            {"uuid": "missing-path"},
            {"path": "/var/archivematica/missing-uuid"},
            {"uuid": "", "path": "/var/archivematica/empty-uuid"},
            {"uuid": "source-c", "path": ""},
        ]

        response = self.client.get(
            reverse("ingest:ingest_metadata_add_files", args=[sip_uuid]),
        )

        assert response.status_code == 200
        assert response.context["editor_payload"] is None
        content = response.content.decode("utf8")
        assert '<div id="md-editor"></div>' not in content
        assert 'id="md-editor-data"' not in content

    def test_ingest_upload_get(self):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        access_target = "description-slug"
        Access.objects.create(
            sipuuid=sip_uuid,
            target=access_target,
        )

        response = self.client.get(
            reverse("ingest:ingest_upload", args=[sip_uuid]),
        )

        assert response.status_code == 200
        assert json.loads(response.content)["target"] == access_target

    def test_ingest_upload_post(self):
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        access_target = "description-slug"

        # Check there is no Access object associated with the SIP yet.
        assert Access.objects.filter(sipuuid=sip_uuid).count() == 0

        response = self.client.post(
            reverse("ingest:ingest_upload", args=[sip_uuid]),
            data={"target": access_target},
        )
        assert response.status_code == 200
        assert json.loads(response.content) == {"ready": True}

        # An Access object was created for the SIP with the right target.
        assert (
            Access.objects.filter(sipuuid=sip_uuid, target=access_target).count() == 1
        )


def test_ingest_upload_as_match_shows_deleted_rows(
    admin_client, dashboard_uuid, caplog
):
    caplog.set_level(logging.DEBUG, "archivematica.dashboard")
    dip_uuid = uuid.uuid4()
    file_uuid = uuid.uuid4()
    resource_id = "/repositories/2/archival_objects/1"
    ArchivesSpaceDIPObjectResourcePairing.objects.create(
        dipuuid=dip_uuid,
        fileuuid=file_uuid,
        resourceid=resource_id,
    )
    ArchivesSpaceDIPObjectResourcePairing.objects.create(
        dipuuid=dip_uuid,
        fileuuid=file_uuid,
        resourceid="/repositories/2/archival_objects/2",
    )

    response = admin_client.delete(
        reverse("ingest:ingest_upload_as_match", kwargs={"uuid": dip_uuid}),
        data=json.dumps({"resource_id": resource_id, "file_uuid": str(file_uuid)}),
        content_type="application/json",
    )
    assert response.status_code == 204

    log_record = caplog.records[0]
    assert log_record.message == f"Resource {resource_id} File {file_uuid} matches 1"


@pytest.mark.django_db
def test_ingest_upload_atk_get_dip_object_paths_uuid_strings(tmp_path, settings):
    settings.WATCH_DIRECTORY = str(tmp_path)
    sip_uuid = uuid.uuid4()
    sip_uuid_str = str(sip_uuid)
    dip_dir_name = f"dip-{sip_uuid}"
    dip_upload_dir = tmp_path / "uploadDIP" / dip_dir_name
    dip_upload_dir.mkdir(parents=True)

    object_paths = ["objects/beta.txt", "objects/alpha.txt"]
    mets_path = dip_upload_dir / f"METS.{sip_uuid}.xml"
    mets_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink">
  <mets:fileSec>
    <mets:fileGrp USE="original">
      <mets:file ID="file1">
        <mets:FLocat xlink:href="{object_paths[0]}" />
      </mets:file>
      <mets:file ID="file2">
        <mets:FLocat xlink:href="{object_paths[1]}" />
      </mets:file>
    </mets:fileGrp>
  </mets:fileSec>
</mets:mets>
""",
        encoding="utf-8",
    )

    sip = models.SIP.objects.create(
        uuid=sip_uuid,
        currentpath=f"{settings.WATCH_DIRECTORY}/uploadDIP/{dip_dir_name}/",
    )
    file_beta = models.File.objects.create(
        sip=sip,
        originallocation=b"origin-beta",
        currentlocation=f"%SIPDirectory%{object_paths[0]}".encode(),
    )
    file_alpha = models.File.objects.create(
        sip=sip,
        originallocation=b"origin-alpha",
        currentlocation=f"%SIPDirectory%{object_paths[1]}".encode(),
    )

    result = ingest_upload_atk_get_dip_object_paths(sip_uuid_str)

    assert result == [
        {"uuid": str(file_alpha.uuid), "path": "alpha.txt"},
        {"uuid": str(file_beta.uuid), "path": "beta.txt"},
    ]
