import uuid
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from archivematica.dashboard.contrib.mcp.client import RPCServerError
from archivematica.dashboard.main import models
from tests.factories import JobFactory


@pytest.fixture()
def transfer(transfer: models.Transfer) -> models.Transfer:
    """The transfer once its processing is done."""
    transfer.status = models.PACKAGE_STATUS_DONE
    transfer.save()

    return transfer


@mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
def test_transfer_list_returns_rpc_summaries(
    mcp_client_cls, dashboard_uuid, admin_client
):
    summary = {
        "uuid": str(uuid.uuid4()),
        "directory": "transfer",
        "timestamp": 1.0,
        "started_at": 1.0,
        "active": True,
        "status": {
            "currentstep": 3,
            "type": "Job",
            "microservicegroup": "Microservice",
        },
        "has_awaiting_decision": False,
        "awaiting_job_uuids": [],
    }
    mcp_client_cls.return_value.get_units_summary.return_value = [summary]
    url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.json() == {"results": [summary]}
    mcp_client_cls.return_value.get_units_summary.assert_called_once_with("Transfer")


@mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
def test_ingest_list_uses_sip_rpc_type(mcp_client_cls, dashboard_uuid, admin_client):
    mcp_client_cls.return_value.get_units_summary.return_value = []
    url = reverse("unit:processing_units", kwargs={"unit_type": "ingest"})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.json() == {"results": []}
    mcp_client_cls.return_value.get_units_summary.assert_called_once_with("SIP")


def test_processing_list_requires_dashboard_authentication(dashboard_uuid, client):
    url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

    response = client.get(url)

    assert response.status_code == 302


def test_processing_list_rejects_non_get_verbs(dashboard_uuid, admin_client):
    url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

    response = admin_client.post(url)

    assert response.status_code == 405


@mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
def test_processing_list_reports_rpc_failure(
    mcp_client_cls, dashboard_uuid, admin_client
):
    mcp_client_cls.return_value.get_units_summary.side_effect = RPCServerError()
    url = reverse("unit:processing_units", kwargs={"unit_type": "transfer"})

    response = admin_client.get(url)

    assert response.status_code == 503
    assert response.json() == {
        "error": True,
        "message": "Unable to fetch processing summaries.",
    }


@mock.patch("archivematica.dashboard.components.unit.views.MCPClient")
def test_job_groups_returns_rpc_results(
    mcp_client_cls, dashboard_uuid, admin_client, transfer
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
    mcp_client_cls, dashboard_uuid, admin_client, transfer
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
    mcp_client_cls, dashboard_uuid, admin_client
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


def test_public_processing_api_is_not_exposed(dashboard_uuid, admin_client):
    response = admin_client.get("/api/v2beta/transfer/")

    assert response.status_code == 404


def test_mark_hidden_rejects_non_admins(dashboard_uuid, client, transfer):
    url = reverse(
        "unit:mark_hidden",
        kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
    )
    resp = client.delete(url)

    assert resp.status_code == 302


def test_mark_hidden_rejects_non_delete_verbs(dashboard_uuid, admin_client, transfer):
    url = reverse(
        "unit:mark_hidden",
        kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
    )
    resp = admin_client.post(url)

    assert resp.status_code == 405


def test_mark_hidden_rejects_unknown_package_types(
    dashboard_uuid, admin_client, transfer
):
    url = f"/tranfser/{transfer.pk}/delete/"
    resp = admin_client.delete(url)

    assert resp.status_code == 404


def test_mark_hidden_conflicts_on_active_packages(
    dashboard_uuid, admin_client, transfer
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
def test_mark_hidden_handles_unknown_errors(
    done, dashboard_uuid, admin_client, transfer
):
    url = reverse(
        "unit:mark_hidden",
        kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
    )
    resp = admin_client.delete(url)

    assert resp.status_code == 500
    assert resp.json() == {"removed": False}


def test_mark_hidden_hides_done_packages(dashboard_uuid, admin_client, transfer):
    url = reverse(
        "unit:mark_hidden",
        kwargs={"unit_type": "transfer", "unit_uuid": transfer.pk},
    )
    resp = admin_client.delete(url)

    assert resp.status_code == 200
    assert resp.json() == {"removed": True}


def test_mark_completed_hidden_rejects_non_admins(dashboard_uuid, client, transfer):
    url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
    resp = client.delete(url)

    assert resp.status_code == 302


def test_mark_completed_hidden_rejects_non_delete_verbs(
    dashboard_uuid, admin_client, transfer
):
    url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
    resp = admin_client.post(url)

    assert resp.status_code == 405


@mock.patch(
    "archivematica.dashboard.components.helpers.completed_units_efficient",
    side_effect=Exception(),
)
def test_mark_completed_hidden_handles_unknown_errors(
    completed_units_efficient, dashboard_uuid, admin_client, transfer
):
    url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
    resp = admin_client.delete(url)

    assert resp.status_code == 500
    assert resp.json() == {"removed": False}


def test_mark_completed_hidden_ignores_active_packages(
    dashboard_uuid, admin_client, transfer
):
    transfer.status = models.PACKAGE_STATUS_PROCESSING
    transfer.save()
    url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
    resp = admin_client.delete(url)

    assert resp.status_code == 200
    assert resp.json() == {"removed": []}


@pytest.mark.parametrize(
    "last_job",
    [
        {"jobtype": "Create SIP from transfer objects"},
        {"jobtype": "Remove the processing directory"},
        {"microservicegroup": "Failed transfer"},
    ],
    ids=["sip_created", "processing_directory_removed", "failed"],
)
def test_mark_completed_hidden_hides_completed_packages(
    dashboard_uuid: uuid.UUID,
    admin_client: Client,
    transfer: models.Transfer,
    make_job: JobFactory,
    last_job: dict[str, str],
) -> None:
    # mark_completed_hidden still relies on job objects.
    make_job(transfer, currentstep=models.Job.STATUS_COMPLETED_SUCCESSFULLY, **last_job)

    url = reverse("unit:mark_all_hidden", kwargs={"unit_type": "transfer"})
    resp = admin_client.delete(url)

    assert resp.status_code == 200
    assert resp.json() == {"removed": [str(transfer.pk)]}
