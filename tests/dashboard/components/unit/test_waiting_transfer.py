import pytest
from django.urls import reverse

from archivematica.dashboard.main import models


@pytest.fixture
def waiting_transfer(db):
    transfer = models.Transfer.objects.create(
        currentlocation="%sharedPath%watchedDirectories/standardTransfer/Waiting/",
        type="standard",
        status=models.PACKAGE_STATUS_PROCESSING,
    )
    assert not models.Job.objects.filter(sipuuid=transfer.pk).exists()
    return transfer


def test_waiting_transfer_supports_detail_and_metadata_navigation_without_jobs(
    dashboard_uuid, admin_client, metadata_applies_to_types, waiting_transfer
):
    detail_url = reverse(
        "unit:detail",
        kwargs={"unit_type": "transfer", "unit_uuid": waiting_transfer.pk},
    )
    metadata_list_url = reverse(
        "transfer:transfer_metadata_list", kwargs={"uuid": waiting_transfer.pk}
    )
    metadata_add_url = reverse(
        "transfer:transfer_metadata_add", kwargs={"uuid": waiting_transfer.pk}
    )

    response = admin_client.get(detail_url)

    assert response.status_code == 200
    content = response.content.decode()
    assert str(waiting_transfer.pk) in content
    assert f'href="{metadata_list_url}"' in content
    assert f'href="{metadata_add_url}"' in content

    response = admin_client.get(metadata_list_url)

    assert response.status_code == 200
    assert list(response.context["metadata"]) == []
    assert f'href="{metadata_add_url}"' in response.content.decode()

    response = admin_client.get(metadata_add_url)

    assert response.status_code == 200
    assert f'action="{metadata_add_url}"' in response.content.decode()
    form = response.context["form"]
    assert not form.is_bound
    assert str(form.instance.metadataappliestoidentifier) == str(waiting_transfer.pk)
    assert form.instance.metadataappliestotype == metadata_applies_to_types["transfer"]
    assert not models.Job.objects.filter(sipuuid=waiting_transfer.pk).exists()


def test_waiting_transfer_cannot_be_removed_before_its_first_job(
    dashboard_uuid, admin_client, waiting_transfer
):
    url = reverse(
        "unit:mark_hidden",
        kwargs={"unit_type": "transfer", "unit_uuid": waiting_transfer.pk},
    )

    response = admin_client.delete(url)

    assert response.status_code == 409
    assert response.json() == {"removed": False}
    waiting_transfer.refresh_from_db()
    assert waiting_transfer.active
    assert not waiting_transfer.hidden
    assert not models.Job.objects.filter(sipuuid=waiting_transfer.pk).exists()
