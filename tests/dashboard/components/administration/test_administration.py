import uuid

import pytest
from components import helpers
from django.urls import reverse
from main.models import Report


@pytest.fixture
@pytest.mark.django_db
def dashboard_uuid():
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.mark.django_db
def test_admin_set_language(dashboard_uuid, admin_client):
    response = admin_client.get(reverse("administration:admin_set_language"))
    assert response.status_code == 200

    assert (
        "Select one of the following languages available:" in response.content.decode()
    )


@pytest.mark.django_db
def test_failure_report_delete(dashboard_uuid, admin_client):
    report = Report.objects.create(content="my report")

    response = admin_client.post(
        reverse("administration:failure_report_delete", args=[report.pk]),
        {"__confirm__": "1"},
        follow=True,
    )
    assert response.status_code == 200

    assert "No reports found." in response.content.decode()
    assert Report.objects.count() == 0


@pytest.mark.django_db
def test_failure_report(dashboard_uuid, admin_client):
    report = Report.objects.create(content="my report")

    response = admin_client.get(reverse("administration:reports_failures_index"))
    assert response.status_code == 200

    content = response.content.decode()
    assert "<h3>Failure report</h3>" in content
    assert reverse("administration:failure_report", args=[report.pk]) in content
