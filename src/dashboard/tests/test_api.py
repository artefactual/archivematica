#!/usr/bin/env python2

import os

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase

from main import models

from components.api import views

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
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'PROCESSING'

    def test_get_unit_status_user_input(self):
        """It should return USER_INPUT."""
        # Setup fixtures
        load_fixture(['job-processing.json', 'jobs-user-input.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'USER_INPUT'

    def test_get_unit_status_failed(self):
        """It should return FAILED."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-failed.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'FAILED'

    def test_get_unit_status_rejected(self):
        """It should return REJECTED."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-rejected.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'REJECTED'

    def test_get_unit_status_completed_transfer(self):
        """It should return COMPLETE and the new SIP UUID."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-complete.json', 'files.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        # Verify
        assert len(status) == 3
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
        assert status['sip_uuid'] == '4060ee97-9c3f-4822-afaf-ebdf838284c3'

    def test_get_unit_status_backlog(self):
        """It should return COMPLETE and in BACKLOG."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-backlog.json'])
        # Test
        status = views.get_unit_status('3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e', 'unitTransfer')
        # Verify
        assert len(status) == 3
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
        assert status['sip_uuid'] == 'BACKLOG'

    def test_get_unit_status_completed_sip(self):
        """It should return COMPLETE."""
        # Setup fixtures
        load_fixture(['jobs-processing.json', 'jobs-transfer-complete.json', 'jobs-sip-complete.json'])
        # Test
        status = views.get_unit_status('4060ee97-9c3f-4822-afaf-ebdf838284c3', 'unitSIP')
        # Verify
        assert len(status) == 2
        assert 'microservice' in status
        assert status['status'] == 'COMPLETE'
