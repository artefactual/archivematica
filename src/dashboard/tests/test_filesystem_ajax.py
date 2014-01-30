#! /usr/bin/python2

# Run from src/dashboard with:
# bash: PYTHONPATH='./src' py.test --ds 'settings.local -v
# fish: env PYTHONPATH='./src' py.test --ds 'settings.local' -v

import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from main import models

class TestSIPArrange(TestCase):

    fixtures = ['test_user.json', 'sip_arrange.json']

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_fixtures(self):
        objs = models.SIPArrange.objects.all()
        assert len(objs) > 0

    def test_arrange_contents_data(self):
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), follow=True)
        expected_json = {
            "directories": [
                "folder",
                "newsip"
            ],
            "entries": [
                "folder",
                "newsip"
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

        # Folder, without /
        response = self.client.get(reverse('components.filesystem_ajax.views.arrange_contents'), {'path': '/arrange/folder'}, follow=True)
        expected_json = {
            "directories": [
                "metadata",
                "objects"
            ],
            "entries": [
                "item_main",
                "metadata",
                "objects"
            ]
        }
        assert response.status_code == 200
        assert json.loads(response.content) == expected_json
