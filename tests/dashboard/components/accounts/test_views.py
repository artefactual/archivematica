import hmac
import uuid
from hashlib import sha1
from typing import Type
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
import pytest_django
from components import helpers
from components.accounts.views import get_oidc_logout_url
from django.contrib.auth.models import User
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from tastypie.models import ApiKey


def test_get_oidc_logout_url_fails_if_token_is_not_set(rf: RequestFactory) -> None:
    request = rf.get("/")
    request.session = {}

    with pytest.raises(ValueError, match="ID token not found in session."):
        get_oidc_logout_url(request)


def test_get_oidc_logout_url_fails_if_logout_endpoint_is_not_set(
    rf: RequestFactory,
) -> None:
    request = rf.get("/")
    request.session = {"oidc_id_token": "mytoken"}

    with pytest.raises(
        ValueError, match="OIDC logout endpoint not configured for provider."
    ):
        get_oidc_logout_url(request)


def test_get_oidc_logout_url_returns_logout_url(
    rf: RequestFactory, settings: pytest_django.fixtures.SettingsWrapper
) -> None:
    settings.OIDC_OP_LOGOUT_ENDPOINT = "http://example.com/logout"
    token = "mytoken"
    request = rf.get("/")
    request.session = {"oidc_id_token": token}

    result = get_oidc_logout_url(request)

    assert result.startswith(settings.OIDC_OP_LOGOUT_ENDPOINT)
    query_dict = parse_qs(urlparse(result).query)
    assert set(query_dict) == {"id_token_hint", "post_logout_redirect_uri"}
    assert query_dict["id_token_hint"] == [token]
    assert query_dict["post_logout_redirect_uri"] == ["http://testserver/"]


@pytest.fixture
def dashboard_uuid() -> None:
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.fixture
def non_administrative_user(django_user_model: Type[User]) -> User:
    return django_user_model.objects.create_user(
        username="test",
        password="test",
        first_name="Foo",
        last_name="Bar",
        email="foobar@example.com",
    )


@pytest.mark.django_db
def test_edit_user_view_denies_access_to_non_admin_users_editing_others(
    dashboard_uuid: None,
    non_administrative_user: User,
    admin_user: User,
    client: Client,
) -> None:
    client.force_login(non_administrative_user)

    response = client.get(
        reverse("accounts:edit", kwargs={"id": admin_user.id}), follow=True
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Forbidden" in content
    assert "You do not have enough access privileges for this operation" in content


@pytest.fixture
def non_administrative_user_apikey(non_administrative_user: User) -> ApiKey:
    return ApiKey.objects.create(user=non_administrative_user)


@pytest.mark.django_db
def test_edit_user_view_renders_user_profile_fields(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    admin_client: Client,
) -> None:
    response = admin_client.get(
        reverse("accounts:edit", kwargs={"id": non_administrative_user.id}), follow=True
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert f"Edit user {non_administrative_user.username}" in content
    assert f'name="username" value="{non_administrative_user.username}"' in content
    assert f'name="first_name" value="{non_administrative_user.first_name}"' in content
    assert f'name="last_name" value="{non_administrative_user.last_name}"' in content
    assert f'name="email" value="{non_administrative_user.email}"' in content
    assert f"<code>{non_administrative_user_apikey.key}</code>" in content


@pytest.mark.django_db
def test_edit_user_view_updates_user_profile_fields(
    dashboard_uuid: None,
    non_administrative_user: User,
    admin_client: Client,
) -> None:
    new_username = "newusername"
    new_password = "newpassword"
    new_first_name = "bar"
    new_last_name = "foo"
    new_email = "newemail@example.com"
    data = {
        "username": new_username,
        "password": new_password,
        "password_confirmation": new_password,
        "first_name": new_first_name,
        "last_name": new_last_name,
        "email": new_email,
    }

    response = admin_client.post(
        reverse("accounts:edit", kwargs={"id": non_administrative_user.id}),
        data,
        follow=True,
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert "Saved" in content
    assert (
        f'<a href="{reverse("accounts:edit", kwargs={"id": non_administrative_user.id})}">{new_username}</a>'
        in content
    )
    assert f"<td>{new_first_name} {new_last_name}</td>" in content
    assert f"<td>{new_email}</td>" in content

    non_administrative_user.refresh_from_db()
    assert non_administrative_user.check_password(new_password)


@pytest.mark.django_db
def test_edit_user_view_regenerates_api_key(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    admin_client: Client,
) -> None:
    data = {
        "username": non_administrative_user.username,
        "first_name": non_administrative_user.first_name,
        "last_name": non_administrative_user.last_name,
        "email": non_administrative_user.email,
        "regenerate_api_key": True,
    }
    expected_uuid = uuid.uuid4()
    expected_key = hmac.new(expected_uuid.bytes, digestmod=sha1).hexdigest()

    with mock.patch("uuid.uuid4", return_value=expected_uuid):
        response = admin_client.post(
            reverse("accounts:edit", kwargs={"id": non_administrative_user.id}),
            data,
            follow=True,
        )
    assert response.status_code == 200

    assert "Saved" in response.content.decode()

    non_administrative_user_apikey.refresh_from_db()
    assert non_administrative_user_apikey.key == expected_key


@pytest.mark.django_db
def test_user_profile_view_allows_users_to_edit_their_profile_fields(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    settings.ALLOW_USER_EDITS = True
    client.force_login(non_administrative_user)

    response = client.get(
        reverse("accounts:profile"),
        follow=True,
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert f"Edit your profile ({non_administrative_user.username})" in content
    assert f'name="username" value="{non_administrative_user.username}"' in content
    assert f'name="first_name" value="{non_administrative_user.first_name}"' in content
    assert f'name="last_name" value="{non_administrative_user.last_name}"' in content
    assert f'name="email" value="{non_administrative_user.email}"' in content
    assert f"<code>{non_administrative_user_apikey.key}</code>" in content


@pytest.mark.django_db
def test_user_profile_view_denies_editing_profile_fields_if_setting_disables_it(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    settings.ALLOW_USER_EDITS = False
    client.force_login(non_administrative_user)

    response = client.get(
        reverse("accounts:profile"),
        follow=True,
    )
    assert response.status_code == 200

    content = response.content.decode()
    assert f"Your profile ({non_administrative_user.username})" in content
    assert f"<dd>{non_administrative_user.username}</dd>" in content
    assert (
        f"<dd>{non_administrative_user.first_name} {non_administrative_user.last_name}</dd>"
        in content
    )
    assert f"<dd>{non_administrative_user.email}</dd>" in content
    assert (
        f'<dd>{"yes" if non_administrative_user.is_superuser else "no"}</dd>' in content
    )
    assert f"<code>{non_administrative_user_apikey.key}</code>" in content


@pytest.mark.django_db
def test_user_profile_view_regenerates_api_key_if_setting_disables_editing(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    settings.ALLOW_USER_EDITS = False
    client.force_login(non_administrative_user)
    data = {"regenerate_api_key": True}
    expected_uuid = uuid.uuid4()
    expected_key = hmac.new(expected_uuid.bytes, digestmod=sha1).hexdigest()

    with mock.patch("uuid.uuid4", return_value=expected_uuid):
        response = client.post(
            reverse("accounts:profile"),
            data,
            follow=True,
        )
    assert response.status_code == 200

    content = response.content.decode()
    assert f"Your profile ({non_administrative_user.username})" in content
    assert f"<dd>{non_administrative_user.username}</dd>" in content
    assert (
        f"<dd>{non_administrative_user.first_name} {non_administrative_user.last_name}</dd>"
        in content
    )
    assert f"<dd>{non_administrative_user.email}</dd>" in content
    assert (
        f'<dd>{"yes" if non_administrative_user.is_superuser else "no"}</dd>' in content
    )
    assert f"<code>{expected_key}</code>" in content


@pytest.mark.django_db
def test_user_profile_view_does_not_regenerate_api_key_if_not_requested(
    dashboard_uuid: None,
    non_administrative_user: User,
    non_administrative_user_apikey: ApiKey,
    client: Client,
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    settings.ALLOW_USER_EDITS = False
    client.force_login(non_administrative_user)

    response = client.post(reverse("accounts:profile"), {}, follow=True)
    assert response.status_code == 200

    content = response.content.decode()
    assert f"Your profile ({non_administrative_user.username})" in content
    assert f"<dd>{non_administrative_user.username}</dd>" in content
    assert (
        f"<dd>{non_administrative_user.first_name} {non_administrative_user.last_name}</dd>"
        in content
    )
    assert f"<dd>{non_administrative_user.email}</dd>" in content
    assert (
        f'<dd>{"yes" if non_administrative_user.is_superuser else "no"}</dd>' in content
    )
    assert f"<code>{non_administrative_user_apikey.key}</code>" in content
