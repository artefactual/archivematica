import os

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
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        helpers.set_setting('dashboard_uuid', 'test-uuid')

    @mock.patch("agentarchives.archivesspace.ArchivesSpaceClient._login")
    def test_get_as_system_client(self, __):
        DashboardSetting.objects.set_dict('upload-archivesspace_v0.0', {
            "base_url": "http://foobar.tld",
            "user": "user",
            "passwd": "12345",
            "repository": "5",
        })
        client = get_as_system_client()
        assert client.base_url == "http://foobar.tld"
        assert client.user == "user"
        assert client.passwd == "12345"
        assert client.repository == "/repositories/5"

        # It raises error when "base_url" is missing.
        DashboardSetting.objects.set_dict('upload-archivesspace_v0.0', {
            "user": "user",
            "passwd": "12345",
            "repository": "5",
        })
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()

        # It raises error when "base_url" is empty.
        DashboardSetting.objects.set_dict('upload-archivesspace_v0.0', {
            "base_url": "",
            "user": "user",
            "passwd": "12345",
            "repository": "5",
        })
        with pytest.raises(ArchivesSpaceError):
            client = get_as_system_client()
