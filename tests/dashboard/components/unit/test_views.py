import uuid
from unittest import mock

import pytest
from components import helpers
from django.urls import reverse
from django.utils import timezone
from main import models


@pytest.fixture()
def install(db):
    helpers.set_setting("dashboard_uuid", "test-uuid")


@pytest.fixture()
def transfer(db):
    return models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation=r"%transferDirectory%",
        status=models.PACKAGE_STATUS_DONE,
    )


@pytest.mark.django_db()
class TestMarkHiddenView:
    def test_it_rejects_non_admins(self, install, client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = client.delete(url)

        assert resp.status_code == 302

    def test_it_rejects_non_delete_verbs(self, install, admin_client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.post(url)

        assert resp.status_code == 405

    def test_it_rejects_unknown_package_types(self, install, admin_client, transfer):
        url = f"/tranfser/{transfer.pk}/delete/"
        resp = admin_client.delete(url)

        assert resp.status_code == 404

    def test_it_conflicts_on_active_packages(self, install, admin_client, transfer):
        transfer.status = models.PACKAGE_STATUS_PROCESSING
        transfer.save()
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 409
        assert resp.json() == {"removed": False}

    @mock.patch("main.models.Transfer.objects.done", side_effect=Exception())
    def test_it_handles_unknown_errors(self, done, install, admin_client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 500
        assert resp.json() == {"removed": False}

    def test_it_hides_done_packages(self, install, admin_client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": True}


@pytest.mark.django_db()
class TestMarkCompletedHiddenView:
    def test_it_rejects_non_admins(self, install, client, transfer):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = client.delete(url)

        assert resp.status_code == 302

    def test_it_rejects_non_delete_verbs(self, install, admin_client, transfer):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.post(url)

        assert resp.status_code == 405

    @mock.patch("components.helpers.completed_units_efficient", side_effect=Exception())
    def test_it_handles_unknown_errors(
        self, completed_units_efficient, install, admin_client, transfer
    ):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 500
        assert resp.json() == {"removed": False}

    def test_it_ignores_active_packages(self, install, admin_client, transfer):
        transfer.status = models.PACKAGE_STATUS_PROCESSING
        transfer.save()
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": []}

    def test_it_hides_done_packages(self, install, admin_client, transfer):
        # mark_completed_hidden still relies on job objects.
        models.Job.objects.create(
            sipuuid=transfer.pk,
            unittype="unitTransfer",
            createdtime=timezone.now(),
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            jobtype="Move transfer to backlog",
        )

        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": [str(transfer.pk)]}

    def test_it_hides_failed_packages(self, install, admin_client, transfer):
        # mark_completed_hidden still relies on job objects.
        models.Job.objects.create(
            sipuuid=transfer.pk,
            unittype="unitTransfer",
            createdtime=timezone.now(),
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            jobtype="Remove the processing directory",
        )

        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": [str(transfer.pk)]}
