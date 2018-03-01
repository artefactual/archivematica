import os
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from lxml import etree

from components.api import views
from components import helpers
from processing import install_builtin_config

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_fixture(fixtures):
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixtures]
    call_command('loaddata', *fixtures, **{'verbosity': 0})


class TestAPI(TestCase):
    """Test API endpoints."""
    fixture_files = ['transfer.json', 'sip.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def test_get_unit_status_processing(self):
        """It should return PROCESSING."""
        # Setup fixtures
        load_fixture(['jobs-processing.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'PROCESSING'
        assert len(completed) == 0

    def test_get_unit_status_user_input(self):
        """It should return USER_INPUT."""
        # Setup fixtures
        load_fixture(['job-processing.json', 'jobs-user-input.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'USER_INPUT'
        assert len(completed) == 0

    def test_get_unit_status_failed(self):
        """It should return FAILED."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-failed.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'FAILED'
        assert len(completed) == 1

    def test_get_unit_status_rejected(self):
        """It should return REJECTED."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-rejected.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'REJECTED'
        assert len(completed) == 0

    def test_get_unit_status_completed_transfer(self):
        """It should return COMPLETE and the new SIP UUID."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-complete.json', 'files.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 3
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
        assert status['sip_uuid'] == '4060ee97-9c3f-4822-afaf-ebdf838284c3'
        assert len(completed) == 1

    def test_get_unit_status_backlog(self):
        """It should return COMPLETE and in BACKLOG."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-backlog.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 3
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
        assert status['sip_uuid'] == 'BACKLOG'
        assert len(completed) == 1

    def test_get_unit_status_completed_sip(self):
        """It should return COMPLETE."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-complete.json', 'jobs-sip-complete.json'])
        # Test
        status = views.get_unit_status('4060ee97-9c3f-4822-afaf-ebdf838284c3', 'unitSIP')
        completed = helpers.completed_units_efficient(unit_type='transfer', include_failed=True)
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
        assert len(completed) == 1


class TestProcessingConfigurationAPI(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        helpers.set_setting('dashboard_uuid', 'test-uuid')
        settings.SHARED_DIRECTORY = tempfile.gettempdir()
        self.config_path = os.path.join(
            settings.SHARED_DIRECTORY,
            'sharedMicroServiceTasksConfigs/processingMCPConfigs/'
        )
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
        install_builtin_config('default')

    def test_get_existing_processing_config(self):
        response = self.client.get(
            reverse('processing_configuration', args=['default']),
            HTTP_ACCEPT='xml'
        )
        assert response.status_code == 200
        assert etree.fromstring(response.content).xpath('.//preconfiguredChoice')

    def test_delete_and_regenerate(self):
        response = self.client.delete(
            reverse('processing_configuration', args=['default']),
        )
        assert response.status_code == 200
        assert not os.path.exists(os.path.join(self.config_path, 'defaultProcessingMCP.xml'))

        response = self.client.get(
            reverse('processing_configuration', args=['default']),
            HTTP_ACCEPT='xml'
        )
        assert response.status_code == 200
        assert etree.fromstring(response.content).xpath('.//preconfiguredChoice')
        assert os.path.exists(os.path.join(self.config_path, 'defaultProcessingMCP.xml'))

    def test_404_for_non_existent_config(self):
        response = self.client.get(
            reverse('processing_configuration', args=['nonexistent']),
            HTTP_ACCEPT='xml'
        )
        assert response.status_code == 404

    def test_404_for_delete_non_existent_config(self):
        response = self.client.delete(
            reverse('processing_configuration', args=['nonexistent']),
        )
        assert response.status_code == 404


class TestAPI2(TestCase):
    """Test API endpoints."""
    fixture_files = ['units.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

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
        load_fixture(['jobs-various.json'])
        completed = helpers.completed_units_efficient(
            unit_type='transfer', include_failed=True)
        print(completed)
        assert len(completed) == 3
        assert '85216028-1150-4321-abb3-31ea570a341b' in completed
        assert '5d0ab97f-a45b-4e0f-9cb6-90ee3a404549' in completed
        assert 'b949773d-7cf7-4c1e-aea5-ccbf65b70ccd' in completed
