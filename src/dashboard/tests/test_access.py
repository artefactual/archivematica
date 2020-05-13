# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import json

from django.urls import reverse
from django.test import TestCase
from django.test.client import Client

from main import models
from components import helpers


class TestAccessAPI(TestCase):
    fixtures = ["test_user", "access"]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_creating_arrange_directory(self):
        record_id = "/repositories/2/archival_objects/2"
        response = self.client.post(
            reverse(
                "access:access_create_directory",
                kwargs={"record_id": record_id.replace("/", "-")},
            ),
            {},
            follow=True,
        )
        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf8"))
        assert response_dict["success"] is True
        mapping = models.SIPArrangeAccessMapping.objects.get(
            system=models.SIPArrangeAccessMapping.ARCHIVESSPACE, identifier=record_id
        )
        assert models.SIPArrange.objects.get(arrange_path=mapping.arrange_path + "/")

    def test_arrange_contents(self):
        record_id = "/repositories/2/archival_objects/1"
        response = self.client.get(
            reverse(
                "access:access_arrange_contents",
                kwargs={"record_id": record_id.replace("/", "-")},
            ),
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "entries" in response_dict
        assert (
            base64.b64encode(b"evelyn_s_photo.jpg").decode("utf8")
            in response_dict["entries"]
        )
        assert len(response_dict["entries"]) == 1
