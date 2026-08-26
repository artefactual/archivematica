import uuid
from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone

from archivematica.dashboard.contrib.mcp.client import RPCServerError
from archivematica.dashboard.main import models


@pytest.fixture()
def transfer(db):
    return models.Transfer.objects.create(
        uuid=uuid.uuid4(),
        currentlocation=r"%transferDirectory%",
        status=models.PACKAGE_STATUS_DONE,
    )


@pytest.mark.django_db()
class TestProcessingMonitorViews:
    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_transfer_list_returns_rpc_units(
        self, mcp_client_cls, dashboard_uuid, admin_client
    ):
        unit = {
            "uuid": "59402c61-3aba-4af7-966a-996073c0601d",
            "directory": "transfer",
            "timestamp": 1.0,
            "active": True,
            "jobs": [],
        }
        mcp_client_cls.return_value.get_transfers_statuses.return_value = [unit]
        url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json() == {"objects": [unit], "mcp": True}
        mcp_client_cls.return_value.get_transfers_statuses.assert_called_once_with()

    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_ingest_list_uses_sip_rpc_type(
        self, mcp_client_cls, dashboard_uuid, admin_client
    ):
        mcp_client_cls.return_value.get_sips_statuses.return_value = []
        url = reverse("unit:processing_units", kwargs={"unit_type": "ingest"})

        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json() == {"objects": [], "mcp": True}
        mcp_client_cls.return_value.get_sips_statuses.assert_called_once_with()

    def test_processing_list_requires_dashboard_authentication(
        self, dashboard_uuid, client
    ):
        url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

        response = client.get(url)

        assert response.status_code == 302

    def test_processing_list_rejects_non_get_verbs(self, dashboard_uuid, admin_client):
        url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

        response = admin_client.post(url)

        assert response.status_code == 405

    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_processing_list_reports_rpc_failure(
        self, mcp_client_cls, dashboard_uuid, admin_client
    ):
        mcp_client_cls.return_value.get_transfers_statuses.side_effect = RPCServerError()
        url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

        response = admin_client.get(url)

        assert response.status_code == 503
        assert response.json() == {
            "error": True,
            "message": "Unable to fetch processing units.",
        }

    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_job_groups_returns_rpc_results(
        self, mcp_client_cls, dashboard_uuid, admin_client, transfer
    ):
        groups = [{"name": "Microservice", "jobs": []}]
        mcp_client_cls.return_value.get_unit_job_groups.return_value = groups
        url = reverse(
            "unit:processing_unit_job_groups",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.uuid},
        )

        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json() == {"results": groups}
        mcp_client_cls.return_value.get_unit_job_groups.assert_called_once_with(
            "Transfer", str(transfer.uuid)
        )

    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_job_groups_rejects_hidden_unit(
        self, mcp_client_cls, dashboard_uuid, admin_client, transfer
    ):
        transfer.hidden = True
        transfer.save()
        url = reverse(
            "unit:processing_unit_job_groups",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.uuid},
        )

        response = admin_client.get(url)

        assert response.status_code == 404
        mcp_client_cls.assert_not_called()

    @mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
    def test_job_groups_rejects_malformed_uuid(
        self, mcp_client_cls, dashboard_uuid, admin_client
    ):
        malformed_uuid = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"
        url = reverse(
            "unit:processing_unit_job_groups",
            kwargs={"unit_type": "transfer", "unit_uuid": malformed_uuid},
        )

        response = admin_client.get(url)

        assert response.status_code == 404
        assert response.json() == {
            "error": True,
            "message": f"Unit with UUID {malformed_uuid} does not exist",
        }
        mcp_client_cls.assert_not_called()

    def test_public_processing_api_is_not_exposed(self, dashboard_uuid, admin_client):
        response = admin_client.get("/api/v2beta/transfer/")

        assert response.status_code == 404


@pytest.mark.django_db()
class TestMarkHiddenView:
    def test_it_rejects_non_admins(self, dashboard_uuid, client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = client.delete(url)

        assert resp.status_code == 302

    def test_it_rejects_non_delete_verbs(self, dashboard_uuid, admin_client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.post(url)

        assert resp.status_code == 405

    def test_it_rejects_unknown_package_types(
        self, dashboard_uuid, admin_client, transfer
    ):
        url = f"/tranfser/{transfer.pk}/delete/"
        resp = admin_client.delete(url)

        assert resp.status_code == 404

    def test_it_conflicts_on_active_packages(
        self, dashboard_uuid, admin_client, transfer
    ):
        transfer.status = models.PACKAGE_STATUS_PROCESSING
        transfer.save()
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 409
        assert resp.json() == {"removed": False}

    @mock.patch(
        "archivematica.dashboard.main.models.Transfer.objects.done",
        side_effect=Exception(),
    )
    def test_it_handles_unknown_errors(
        self, done, dashboard_uuid, admin_client, transfer
    ):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 500
        assert resp.json() == {"removed": False}

    def test_it_hides_done_packages(self, dashboard_uuid, admin_client, transfer):
        url = reverse(
            "unit:mark_hidden",
            kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
        )
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": True}


@pytest.mark.django_db()
class TestMarkCompletedHiddenView:
    def test_it_rejects_non_admins(self, dashboard_uuid, client, transfer):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = client.delete(url)

        assert resp.status_code == 302

    def test_it_rejects_non_delete_verbs(self, dashboard_uuid, admin_client, transfer):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.post(url)

        assert resp.status_code == 405

    @mock.patch(
        "archivematica.dashboard.components.helpers.completed_units_efficient",
        side_effect=Exception(),
    )
    def test_it_handles_unknown_errors(
        self, completed_units_efficient, dashboard_uuid, admin_client, transfer
    ):
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 500
        assert resp.json() == {"removed": False}

    def test_it_ignores_active_packages(self, dashboard_uuid, admin_client, transfer):
        transfer.status = models.PACKAGE_STATUS_PROCESSING
        transfer.save()
        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": []}

    def test_it_hides_done_packages(self, dashboard_uuid, admin_client, transfer):
        # mark_completed_hidden still relies on job objects.
        models.Job.objects.create(
            sipuuid=transfer.pk,
            unittype="unitTransfer",
            createdtime=timezone.now(),
            currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            jobtype="Create SIP from transfer objects",
        )

        url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
        resp = admin_client.delete(url)

        assert resp.status_code == 200
        assert resp.json() == {"removed": [str(transfer.pk)]}

    def test_it_hides_failed_packages(self, dashboard_uuid, admin_client, transfer):
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
