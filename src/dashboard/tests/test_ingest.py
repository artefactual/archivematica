import os

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
import mock
import pytest

from agentarchives.archivesspace import ArchivesSpaceError
from components import helpers
from components.ingest.views_as import get_as_system_client
from main.models import DashboardSetting

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestIngest(TestCase):
    fixture_files = ["test_user.json", "sip.json", "jobs-sip-complete.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

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
        url = reverse(
            "components.ingest.views.ingest_metadata_event_detail", args=[sip_uuid]
        )
        response = self.client.get(url)
        assert response.status_code == 200
        title = "".join(
            ["<h1>" "Normalization Event Detail<br />", "<small>test</small>", "</h1>"]
        )
        assert title in response.content

    def test_add_metadata_files_view(self):
        """Test the 'Add metadata files' view of a SIP"""
        sip_uuid = "4060ee97-9c3f-4822-afaf-ebdf838284c3"
        url = reverse(
            "components.ingest.views.ingest_metadata_add_files", args=[sip_uuid]
        )
        response = self.client.get(url)
        assert response.status_code == 200
        title = "\n    ".join(
            ["<h1>", "  Add metadata files<br />", "  <small>test</small>", "</h1>"]
        )
        assert title in response.content
