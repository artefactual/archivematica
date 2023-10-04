import pytest
from components import helpers
from django.urls import reverse


@pytest.mark.django_db
def test_admin_set_language(admin_client):
    helpers.set_setting("dashboard_uuid", "test-uuid")

    response = admin_client.get(reverse("administration:admin_set_language"))
    assert response.status_code == 200

    assert (
        "Select one of the following languages available:" in response.content.decode()
    )
