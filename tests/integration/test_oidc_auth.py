import os
import uuid
from typing import Type

import pytest
from components import helpers
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Page
from pytest_django.fixtures import SettingsWrapper
from pytest_django.live_server_helper import LiveServer

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.fixture
def dashboard_uuid() -> None:
    helpers.set_setting("dashboard_uuid", str(uuid.uuid4()))


@pytest.fixture
def user(django_user_model: Type[User]) -> User:
    user = django_user_model.objects.create(
        username="foobar",
        email="foobar@example.com",
        first_name="Foo",
        last_name="Bar",
    )
    user.set_password("foobar1A,")
    user.save()

    return user


@pytest.mark.django_db
def test_oidc_backend_creates_local_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: None,
    django_user_model: Type[User],
) -> None:
    page.goto(live_server.url)

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("demo@example.com")
    page.get_by_label("Password", exact=True).fill("demo")
    page.get_by_role("button", name="Sign In").click()

    assert page.url == f"{live_server.url}/transfer/"
    page.get_by_text("demo@example.com").click()
    page.get_by_role("link", name="Your profile").click()

    assert page.url == f"{live_server.url}{reverse('accounts:profile')}"
    assert [
        i.strip()
        for i in page.locator("dl.dl-horizontal").text_content().splitlines()
        if i.strip()
    ] == [
        "Username",
        "demo@example.com",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]

    assert (
        django_user_model.objects.filter(
            username="demo@example.com", first_name="Demo", last_name="User"
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_local_authentication_backend_authenticates_existing_user(
    page: Page, live_server: LiveServer, dashboard_uuid: None, user: User
) -> None:
    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_text("Log in", exact=True).click()

    assert page.url == f"{live_server.url}/transfer/"

    page.get_by_text("foobar").click()
    page.get_by_role("link", name="Your profile").click()

    assert page.url == f"{live_server.url}{reverse('accounts:profile')}"
    assert [
        i.strip()
        for i in page.locator("dl.dl-horizontal").text_content().splitlines()
        if i.strip()
    ] == [
        "Username",
        "foobar",
        "Name",
        "Foo Bar",
        "E-mail",
        "foobar@example.com",
        "Admin",
        "no",
    ]


@pytest.mark.django_db
def test_removing_model_authentication_backend_disables_local_authentication(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: None,
    user: User,
    settings: SettingsWrapper,
) -> None:
    disabled_backends = ["django.contrib.auth.backends.ModelBackend"]
    settings.AUTHENTICATION_BACKENDS = [
        b for b in settings.AUTHENTICATION_BACKENDS if b not in disabled_backends
    ]

    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_text("Log in", exact=True).click()

    assert page.url == f"{live_server.url}{settings.LOGIN_URL}"
    assert (
        "Please enter a correct username and password"
        in page.locator("div.alert").text_content().strip()
    )


@pytest.mark.django_db
def test_setting_login_url_redirects_to_oidc_login_page(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: None,
    user: User,
    settings: SettingsWrapper,
) -> None:
    page.goto(live_server.url)
    assert page.url == f"{live_server.url}{reverse('accounts:login')}"

    settings.LOGIN_URL = reverse("oidc_authentication_init")

    page.goto(live_server.url)

    assert page.url.startswith(settings.OIDC_OP_AUTHORIZATION_ENDPOINT)


@pytest.mark.django_db
def test_setting_request_parameter_in_local_login_url_redirects_to_secondary_provider(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: None,
    settings: SettingsWrapper,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("support@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    assert page.url == f"{live_server.url}/transfer/"
    page.get_by_text("support@example.com").click()
    page.get_by_role("link", name="Your profile").click()

    assert page.url == f"{live_server.url}{reverse('accounts:profile')}"
    assert [
        i.strip()
        for i in page.locator("dl.dl-horizontal").text_content().splitlines()
        if i.strip()
    ] == [
        "Username",
        "support@example.com",
        "Name",
        "Support User",
        "E-mail",
        "support@example.com",
        "Admin",
        "no",
    ]


@pytest.mark.django_db
def test_logging_out_logs_out_user_from_secondary_provider(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: None,
    settings: SettingsWrapper,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("support@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    assert page.url == f"{live_server.url}/transfer/"

    # Logging out redirects the user to the login url.
    page.get_by_text("support@example.com").click()
    page.get_by_role("link", name="Log out").click()
    assert page.url == f"{live_server.url}{reverse('accounts:login')}"

    # Logging in through the OIDC provider requires to authenticate again.
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )
    page.get_by_role("link", name="Log in with OpenID Connect").click()
    assert page.url.startswith(
        settings.OIDC_PROVIDERS["SECONDARY"]["OIDC_OP_AUTHORIZATION_ENDPOINT"]
    )
