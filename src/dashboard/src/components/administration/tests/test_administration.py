import pytest
from components import helpers
from django.urls import reverse
from main.models import Report


@pytest.mark.django_db
def test_admin_set_language(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.get(reverse("administration:admin_set_language"))
    assert response.status_code == 200

    assert (
        "Select one of the following languages available:" in response.content.decode()
    )


@pytest.mark.django_db
def test_failure_report_delete(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")
    report = Report.objects.create(content="my report")

    response = admin_client.post(
        reverse("administration:failure_report_delete", args=[report.pk]),
        {"__confirm__": "1"},
        follow=True,
    )
    assert response.status_code == 200

    assert "No reports found." in response.content.decode()
    assert Report.objects.count() == 0
