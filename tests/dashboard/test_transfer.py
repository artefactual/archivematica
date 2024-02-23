import pathlib

import pytest
from components import helpers
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from main.models import DublinCore
from main.models import TransferMetadataFieldValue

TEST_USER_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "test_user.json"
TRANSFER_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "transfer.json"


class TestTransferViews(TestCase):
    fixtures = [TEST_USER_FIXTURE, TRANSFER_FIXTURE]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_metadata_edit(self):
        """Test the metadata form of a transfer"""
        transfer_uuid = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"
        url = reverse("transfer:transfer_metadata_add", args=[transfer_uuid])
        # Post metadata in Spanish
        response = self.client.post(
            url,
            {
                "title": "Mi pequeña transferencia",
                "is_part_of": "1234aéiou",
                "creator": "El Creador",
                "subject": "Un Tema",
                "description": "La Descripción",
                "publisher": "El Publicista",
                "contributor": "Un colaborador",
                "date": "2019-01-01",
            },
        )
        # Verify changes
        transfer_metadata = DublinCore.objects.get(
            metadataappliestoidentifier=transfer_uuid
        )
        assert transfer_metadata.title == "Mi pequeña transferencia"
        assert transfer_metadata.is_part_of == "AIC#1234aéiou"
        assert transfer_metadata.creator == "El Creador"
        assert transfer_metadata.subject == "Un Tema"
        assert transfer_metadata.description == "La Descripción"
        assert transfer_metadata.publisher == "El Publicista"
        assert transfer_metadata.contributor == "Un colaborador"
        assert transfer_metadata.date == "2019-01-01"
        # Verify form redirects to the metadata list after saving
        redirect_url = reverse("transfer:transfer_metadata_list", args=[transfer_uuid])
        assert response.url == redirect_url


@pytest.mark.django_db
def test_component_get(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    # This TransferMetadataSet is going to be created in the view.
    transfer_uuid = "43965fdb-37f3-4ec8-aa67-b49b2733f88a"

    response = admin_client.get(
        reverse("transfer:component", args=[transfer_uuid]),
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Image fixity" in content
    assert "Media number" in content
    assert "Serial number" in content


# @pytest.mark.django_db
def test_component_post(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    # This TransferMetadataSet is going to be created in the view.
    transfer_uuid = "43965fdb-37f3-4ec8-aa67-b49b2733f88a"

    # Verify there are no field values for the metadata set.
    assert TransferMetadataFieldValue.objects.filter(set=transfer_uuid).count() == 0

    response = admin_client.post(
        reverse("transfer:component", args=[transfer_uuid]),
        data={"media_format": '3.5" floppy', "media_number": "123"},
        follow=True,
    )
    assert response.status_code == 200

    assert "Metadata saved." in response.content.decode()
    assert set(
        TransferMetadataFieldValue.objects.filter(
            set=transfer_uuid, field__fieldname__in=["media_format", "media_number"]
        ).values_list("fieldvalue")
    ) == {('3.5" floppy',), ("123",)}
