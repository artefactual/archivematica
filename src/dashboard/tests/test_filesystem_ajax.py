#! /usr/bin/python2

import base64
import json
import os

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestSIPArrange(TestCase):

    fixture_files = ['test_user.json', 'sip_arrange.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_fixtures(self):
        objs = models.SIPArrange.objects.all()
        assert len(objs) > 0

    def test_arrange_contents_data(self):
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': None}, follow=True)
        # Order of response lists not guaranteed - this is set to be the same as the response
        expected_json = {
            "directories": [
                base64.b64encode("newsip"),
                base64.b64encode("toplevel"),
            ],
            "entries": [
                base64.b64encode("newsip"),
                base64.b64encode("toplevel"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

        # Folder, without /
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': base64.b64encode('/arrange/newsip/objects/')}, follow=True)
        expected_json = {
            "directories": [
                base64.b64encode("evelyn_s_second_photo"),
            ],
            "entries": [
                base64.b64encode("evelyn_s_photo.jpg"),
                base64.b64encode("evelyn_s_second_photo"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

    def test_delete_arranged_files(self):
        # Delete files
        response = self.client.post(reverse('components.filesystem_ajax.views.delete_arrange'), data={'filepath': base64.b64encode('/arrange/newsip/')}, follow=True)
        assert response.status_code == 200
        assert json.loads(response.content) == {'message': 'Delete successful.'}
        # Check deleted
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': base64.b64encode('/arrange')}, follow=True)
        expected_json = {
            "directories": [
                base64.b64encode("toplevel"),
            ],
            "entries": [
                base64.b64encode("toplevel"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

    def test_create_arranged_directory(self):
        # Create directory
        response = self.client.post(reverse('components.filesystem_ajax.views.create_directory_within_arrange'), data={'path': base64.b64encode('/arrange/new_dir')}, follow=True)
        assert response.status_code == 200
        assert json.loads(response.content) == {'message': 'Creation successful.'}
        # Check created
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': base64.b64encode('/arrange')}, follow=True)
        expected_json = {
            "directories": [
                base64.b64encode("newsip"),
                base64.b64encode("new_dir"),
                base64.b64encode("toplevel"),
            ],
            "entries": [
                base64.b64encode("newsip"),
                base64.b64encode("new_dir"),
                base64.b64encode("toplevel"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

    def test_move_within_arrange(self):
        # Move directory
        response = self.client.post(reverse('components.filesystem_ajax.views.move_within_arrange'), data={'filepath': base64.b64encode('/arrange/newsip/'), 'destination': base64.b64encode('/arrange/toplevel/')}, follow=True)
        assert response.status_code == 200
        assert json.loads(response.content) == {'message': 'SIP files successfully moved.'}
        # Check gone from parent
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': base64.b64encode('/arrange')}, follow=True)
        expected_json = {
            "directories": [
                base64.b64encode("toplevel"),
            ],
            "entries": [
                base64.b64encode("toplevel"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json
        # Check now in subdirectory
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': base64.b64encode('/arrange/toplevel')}, follow=True)
        expected_json = {
            "directories": [
                base64.b64encode("newsip"),
                base64.b64encode("subsip"),
            ],
            "entries": [
                base64.b64encode("newsip"),
                base64.b64encode("subsip"),
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json
