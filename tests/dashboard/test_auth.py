import json

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects
from tastypie.models import ApiKey

from archivematica.dashboard.components.helpers import generate_api_key

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


API_URL_NAMES = ["api:completed_transfers", "api:completed_ingests"]


@pytest.fixture
def user(django_user_model: type[User]) -> User:
    return django_user_model.objects.create_superuser(username="test", password="test")


@pytest.mark.parametrize(
    "url",
    [
        reverse("transfer:transfer_index"),
        reverse("ingest:ingest_index"),
        reverse("administration:api"),
        reverse("administration:general"),
        reverse("administration:premis_agent"),
        # Verify that exempted URLs cannot be used to access other areas
        # that are restricted.
        "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "transfer/"),
        "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "abcdefgh/api/"),
        "{}/{}".format(settings.LOGIN_URL.rstrip("/"), "version"),
    ],
)
def test_site_requires_auth(client: Client, url: str) -> None:
    response = client.get(url)

    assertRedirects(response, settings.LOGIN_URL)


@pytest.mark.parametrize(
    "url_name",
    ["transfer:transfer_index", "ingest:ingest_index", "administration:api"],
)
def test_site_performs_session_auth(client: Client, user: User, url_name: str) -> None:
    assert client.login(username="test", password="test")

    response = client.get(reverse(url_name), follow=False)

    assert response.status_code == 200


@pytest.mark.parametrize("url_name", API_URL_NAMES)
def test_api_requires_auth(client: Client, url_name: str) -> None:
    response = client.get(reverse(url_name))

    assert response.status_code == 403
    assert response.content.decode("utf8") == json.dumps(
        {"message": "API key not valid.", "error": True}
    )


@pytest.mark.parametrize("url_name", API_URL_NAMES)
def test_api_authenticates_via_key(client: Client, user: User, url_name: str) -> None:
    generate_api_key(user)
    key = ApiKey.objects.get(user=user).key

    response = client.get(
        reverse(url_name),
        headers={"authorization": f"ApiKey {user.username}:{key}"},
        follow=False,
    )

    assert response.status_code == 200


@pytest.mark.parametrize("url_name", API_URL_NAMES)
def test_api_authenticates_via_session(
    client: Client, user: User, url_name: str
) -> None:
    assert client.login(username="test", password="test")

    response = client.get(reverse(url_name), follow=False)

    assert response.status_code == 200
