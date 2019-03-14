# -*- coding: utf-8 -*-
import os

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from components import helpers
from main.models import DublinCore


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTransferViews(TestCase):
    fixture_files = ["test_user.json", "transfer.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_metadata_edit(self):
        """Test the metadata form of a transfer"""
        transfer_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        url = reverse(
            "components.transfer.views.transfer_metadata_edit", args=[transfer_uuid]
        )
        # Post metadata in Spanish
        response = self.client.post(
            url,
            {
                "title": u"Mi pequeña transferencia",
                "is_part_of": u"1234aéiou",
                "creator": "El Creador",
                "subject": "Un Tema",
                "description": u"La Descripción",
                "publisher": "El Publicista",
                "contributor": "Un colaborador",
                "date": "2019-01-01",
            },
        )
        # Verify changes
        transfer_metadata = DublinCore.objects.get(
            metadataappliestoidentifier=transfer_uuid
        )
        assert transfer_metadata.title == u"Mi pequeña transferencia"
        assert transfer_metadata.is_part_of == u"AIC#1234aéiou"
        assert transfer_metadata.creator == "El Creador"
        assert transfer_metadata.subject == "Un Tema"
        assert transfer_metadata.description == u"La Descripción"
        assert transfer_metadata.publisher == "El Publicista"
        assert transfer_metadata.contributor == "Un colaborador"
        assert transfer_metadata.date == "2019-01-01"
        # Verify form redirects to the metadata list after saving
        redirect_url = response.wsgi_request.build_absolute_uri(
            reverse(
                "components.transfer.views.transfer_metadata_list", args=[transfer_uuid]
            )
        )
        assert response.url == redirect_url
