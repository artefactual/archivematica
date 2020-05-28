# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from components import helpers


class TestBacklogAPI(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")
        self.data = '{"time":1586880124134,"columns":[{"visible":true},{"visible":true},{"visible":true},{"visible":false},{"visible":false},{"visible":true},{"visible":false},{"visible":true}]}'

    def test_save_datatable_state(self):
        """Test ability to save DataTable state"""
        response = self.client.post(
            "/backlog/save_state/transfers/", self.data, content_type="application/json"
        )
        assert response.status_code == 200
        saved_state = helpers.get_setting("transfers_datatable_state")
        assert json.dumps(self.data) == saved_state

    def test_load_datatable_state(self):
        """Test ability to load DataTable state"""
        helpers.set_setting("transfers_datatable_state", json.dumps(self.data))
        # Retrieve data from view
        response = self.client.get(reverse("backlog:load_state", args=["transfers"]))
        assert response.status_code == 200
        payload = json.loads(response.content.decode("utf8"))
        assert payload["time"] == 1586880124134
        assert payload["columns"][0]["visible"] is True
        assert payload["columns"][3]["visible"] is False

    def test_load_datatable_state_404(self):
        """Non-existent settings should return a 404"""
        response = self.client.get(reverse("backlog:load_state", args=["nonexistent"]))
        assert response.status_code == 404
        payload = json.loads(response.content.decode("utf8"))
        assert payload["error"] is True
        assert payload["message"] == "Setting not found"
