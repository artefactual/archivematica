import uuid

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from archivematica.dashboard.main.models import DublinCore
from archivematica.dashboard.main.models import MetadataAppliesToType
from archivematica.dashboard.main.models import Taxonomy
from archivematica.dashboard.main.models import TaxonomyTerm
from archivematica.dashboard.main.models import Transfer
from archivematica.dashboard.main.models import TransferMetadataField
from archivematica.dashboard.main.models import TransferMetadataFieldValue
from tests.factories import TransferFactory

# UUID of the transfer of the transfer fixture.
TRANSFER_UUID = "3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e"


@pytest.fixture
def transfer(make_transfer: TransferFactory) -> Transfer:
    """A completed standard transfer named "test"."""
    return make_transfer(
        uuid=uuid.UUID(TRANSFER_UUID),
        type="Standard",
        currentlocation=(
            "%sharedPath%watchedDirectories/SIPCreation/completedTransfers/"
            f"test-{TRANSFER_UUID}/"
        ),
    )


def test_metadata_edit(
    admin_client: Client,
    dashboard_uuid: uuid.UUID,
    transfer: Transfer,
    metadata_applies_to_types: dict[str, MetadataAppliesToType],
) -> None:
    """Test the metadata form of a transfer"""
    url = reverse("transfer:transfer_metadata_add", args=[transfer.uuid])

    # Post metadata in Spanish
    response = admin_client.post(
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
        metadataappliestoidentifier=transfer.uuid
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
    assertRedirects(
        response,
        reverse("transfer:transfer_metadata_list", args=[transfer.uuid]),
        fetch_redirect_response=False,
    )


@pytest.mark.django_db
def test_component_get(admin_client, dashboard_uuid):
    # This TransferMetadataSet is going to be created in the view.
    transfer_uuid = "43965fdb-37f3-4ec8-aa67-b49b2733f88a"
    TransferMetadataField.objects.create(fieldlabel="Image fixity")
    TransferMetadataField.objects.create(fieldlabel="Media number")
    TransferMetadataField.objects.create(fieldlabel="Serial number")

    response = admin_client.get(
        reverse("transfer:component", args=[transfer_uuid]),
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Image fixity" in content
    assert "Media number" in content
    assert "Serial number" in content


# @pytest.mark.django_db
def test_component_post(admin_client, dashboard_uuid):
    # This TransferMetadataSet is going to be created in the view.
    transfer_uuid = "43965fdb-37f3-4ec8-aa67-b49b2733f88a"
    taxonomy = Taxonomy.objects.create(name="Disk media formats")
    TaxonomyTerm.objects.create(term='3.5" floppy', taxonomy=taxonomy)
    TransferMetadataField.objects.create(
        fieldlabel="Media format",
        fieldname="media_format",
        optiontaxonomy=taxonomy,
    )
    TransferMetadataField.objects.create(
        fieldlabel="Media number", fieldname="media_number"
    )

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
