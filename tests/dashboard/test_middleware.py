import uuid
from collections.abc import Iterator

import pytest
import pytest_django
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client
from django.test import override_settings
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from archivematica.dashboard.installer.middleware import _load_exempt_urls
from archivematica.dashboard.middleware.common import (
    CustomShibbolethRemoteUserMiddleware,
)

AUDIT_LOG_MIDDLEWARE = "archivematica.dashboard.middleware.common.AuditLogMiddleware"
OIDC_CAPTURE_QUERY_PARAM_MIDDLEWARE = (
    "archivematica.dashboard.middleware.common.OidcCaptureQueryParamMiddleware"
)


# ConfigurationCheckMiddleware of the installer


@pytest.mark.usefixtures("admin_user")
def test_user_is_sent_to_installer(client: Client) -> None:
    response = client.get("/")

    assertRedirects(response, reverse("installer:welcome"))


@pytest.mark.usefixtures("admin_user")
def test_installer(client: Client) -> None:
    response = client.get(reverse("installer:welcome"))

    assert response.status_code == 200


@pytest.fixture
def exempt_url() -> Iterator[str]:
    """A path that unauthenticated users can access."""
    with override_settings(LOGIN_EXEMPT_URLS=[r"^foobar"]):
        _load_exempt_urls()
        yield "foobar"
    # The installer middleware keeps the exempt URLs in a module-level list
    # built from the settings, so rebuild it from the restored settings.
    _load_exempt_urls()


def test_unauthenticated_user_can_access_exempt_url(
    client: Client, dashboard_uuid: uuid.UUID, exempt_url: str
) -> None:
    response = client.get(exempt_url)

    assert response.status_code == 404


@pytest.mark.skipif(
    settings.CAS_AUTHENTICATION,
    reason="CAS authentication sends unauthenticated users to the CAS server",
)
def test_unauthenticated_user_is_sent_to_login_page(
    client: Client, dashboard_uuid: uuid.UUID
) -> None:
    response = client.get(reverse("main:main_index"))

    assertRedirects(response, settings.LOGIN_URL)


def test_authenticated_user_passes(
    admin_client: Client, dashboard_uuid: uuid.UUID
) -> None:
    response = admin_client.get(reverse("transfer:transfer_index"))

    assert response.status_code == 200


# AuditLogMiddleware


def test_audit_log_middleware_adds_username(
    settings: pytest_django.Settings, client: Client, django_user_model: type[User]
) -> None:
    """Test that X-Username is added for authenticated users."""
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, AUDIT_LOG_MIDDLEWARE]
    user = django_user_model.objects.create_user(username="testclient", password="test")
    client.force_login(user)

    response = client.get("/transfer/", follow=True)

    assert response.has_header("X-Username")
    assert response["X-Username"] == user.username


@pytest.mark.django_db
def test_audit_log_middleware_unauthenticated(
    settings: pytest_django.Settings, client: Client, django_user_model: type[User]
) -> None:
    """Test absence of X-Username header once the user has logged out."""
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, AUDIT_LOG_MIDDLEWARE]
    user = django_user_model.objects.create_user(username="testclient", password="test")
    client.force_login(user)
    client.logout()

    response = client.get(settings.LOGIN_URL, follow=True)

    assert not response.has_header("X-Username")


# OidcCaptureQueryParamMiddleware


def test_middleware_stores_provider_name_in_session(
    settings: pytest_django.Settings, client: Client, dashboard_uuid: uuid.UUID
) -> None:
    settings.OIDC_PROVIDERS = {"MYPROVIDER": {}}
    settings.OIDC_PROVIDER_QUERY_PARAM_NAME = "myparameter"
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, OIDC_CAPTURE_QUERY_PARAM_MIDDLEWARE]

    # The middleware class converts the provider name to uppercase.
    response = client.get(settings.LOGIN_URL, {"myparameter": "myprovider"})

    assert response.status_code == 200
    assert client.session["providername"] == "MYPROVIDER"


# CustomShibbolethRemoteUserMiddleware


@pytest.fixture
def shibboleth_middleware(
    settings: pytest_django.Settings,
) -> CustomShibbolethRemoteUserMiddleware:
    settings.SHIBBOLETH_ADMIN_ENTITLEMENT = "preservation-admin"

    return CustomShibbolethRemoteUserMiddleware(lambda request: HttpResponse())


@pytest.fixture
def shibboleth_user(django_user_model: type[User]) -> User:
    return django_user_model.objects.create(username="demo@example.com")


@pytest.mark.parametrize(
    "entitlement, is_superuser",
    [
        pytest.param("preservation-admin", True, id="admin-entitlement"),
        pytest.param(
            "preservation-user;preservation-admin;preservation-manager",
            True,
            id="admin-entitlement-among-others",
        ),
        pytest.param(
            "preservation-user;preservation-manager", False, id="other-entitlements"
        ),
        pytest.param("preservation-administrator", False, id="partial-match"),
    ],
)
def test_make_profile_maps_admin_entitlement_to_superuser(
    shibboleth_middleware: CustomShibbolethRemoteUserMiddleware,
    shibboleth_user: User,
    entitlement: str,
    is_superuser: bool,
) -> None:
    shibboleth_middleware.make_profile(shibboleth_user, {"entitlement": entitlement})

    shibboleth_user.refresh_from_db()
    assert shibboleth_user.is_superuser is is_superuser


def test_make_profile_revokes_superuser_without_admin_entitlement(
    shibboleth_middleware: CustomShibbolethRemoteUserMiddleware,
    shibboleth_user: User,
) -> None:
    shibboleth_user.is_superuser = True
    shibboleth_user.save()

    shibboleth_middleware.make_profile(
        shibboleth_user, {"entitlement": "preservation-user"}
    )

    shibboleth_user.refresh_from_db()
    assert not shibboleth_user.is_superuser
