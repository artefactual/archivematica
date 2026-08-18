import os
import uuid

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django import Settings
from pytest_django.live_server_helper import LiveServer

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)

if not django_settings.CAS_AUTHENTICATION:
    pytest.skip("Skipping CAS integration tests", allow_module_level=True)


def open_user_menu(page: Page) -> None:
    user_menu = page.locator("li.user.dropdown")
    expect(user_menu).to_be_visible()
    user_menu.evaluate("node => node.classList.add('open')")


def click_profile_from_user_menu(page: Page) -> None:
    open_user_menu(page)
    page.get_by_role("link", name="Your profile").click()


def click_logout_from_user_menu(page: Page) -> None:
    open_user_menu(page)
    page.get_by_role("button", name="Log out").click()


def log_in_via_cas(
    page: Page, live_server: LiveServer, username: str, password: str
) -> None:
    page.goto(live_server.url)
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    page.locator("button[name=submitBtn]").click()


def get_profile_details(page: Page, live_server: LiveServer) -> list[str]:
    click_profile_from_user_menu(page)

    assert page.url == f"{live_server.url}{reverse('accounts:profile')}"
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None

    return [i.strip() for i in details_text.splitlines() if i.strip()]


@pytest.fixture
def check_admin_attributes(settings: Settings) -> Settings:
    settings.CAS_CHECK_ADMIN_ATTRIBUTES = True
    settings.CAS_ADMIN_ATTRIBUTE = "memberOf"
    settings.CAS_ADMIN_ATTRIBUTE_VALUE = "administrators"

    return settings


@pytest.mark.django_db
def test_login_redirects_to_cas_server_login_page(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID, settings: Settings
) -> None:
    page.goto(live_server.url)

    assert page.url.startswith(f"{settings.CAS_SERVER_URL}login")
    expect(page.locator("#username")).to_be_visible()


@pytest.mark.django_db
def test_cas_backend_creates_local_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    log_in_via_cas(page, live_server, "demo", "test")

    assert page.url == f"{live_server.url}/transfer/"
    assert get_profile_details(page, live_server) == [
        "Username",
        "demo",
        "Name",
        "E-mail",
        "Admin",
        "no",
    ]

    user = django_user_model.objects.get(username="demo")
    assert not user.is_superuser


@pytest.mark.django_db
def test_cas_backend_authenticates_existing_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    django_user_model.objects.create(
        username="demo",
        email="demo@example.com",
        first_name="Demo",
        last_name="User",
    )

    log_in_via_cas(page, live_server, "demo", "test")

    assert page.url == f"{live_server.url}/transfer/"
    assert get_profile_details(page, live_server) == [
        "Username",
        "demo",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]

    assert django_user_model.objects.filter(username="demo").count() == 1


@pytest.mark.django_db
def test_admin_attribute_grants_administrator_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    check_admin_attributes: Settings,
) -> None:
    # The admin user is a member of multiple CAS groups, so the memberOf
    # attribute is parsed as a list.
    log_in_via_cas(page, live_server, "admin", "test")

    assert page.url == f"{live_server.url}/transfer/"
    assert get_profile_details(page, live_server) == [
        "Username",
        "admin",
        "Name",
        "E-mail",
        "Admin",
        "yes",
    ]

    user = django_user_model.objects.get(username="admin")
    assert user.is_superuser


@pytest.mark.django_db
def test_single_valued_admin_attribute_grants_administrator_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    check_admin_attributes: Settings,
) -> None:
    # The sysadmin user is a member of a single CAS group, so the memberOf
    # attribute is parsed as a string.
    log_in_via_cas(page, live_server, "sysadmin", "test")

    assert page.url == f"{live_server.url}/transfer/"

    user = django_user_model.objects.get(username="sysadmin")
    assert user.is_superuser


@pytest.mark.django_db
def test_missing_admin_attribute_removes_administrator_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    check_admin_attributes: Settings,
) -> None:
    django_user_model.objects.create(username="demo", is_superuser=True)

    log_in_via_cas(page, live_server, "demo", "test")

    assert page.url == f"{live_server.url}/transfer/"
    assert get_profile_details(page, live_server) == [
        "Username",
        "demo",
        "Name",
        "E-mail",
        "Admin",
        "no",
    ]

    user = django_user_model.objects.get(username="demo")
    assert not user.is_superuser


@pytest.mark.django_db
def test_autoconfigure_email_sets_email_of_new_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    settings.CAS_AUTOCONFIGURE_EMAIL = True
    settings.CAS_EMAIL_DOMAIN = "example.com"

    log_in_via_cas(page, live_server, "demo", "test")

    assert page.url == f"{live_server.url}/transfer/"
    assert get_profile_details(page, live_server) == [
        "Username",
        "demo",
        "Name",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]

    user = django_user_model.objects.get(username="demo")
    assert user.email == "demo@example.com"


@pytest.mark.django_db
def test_logging_out_logs_out_user_from_cas_server(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID, settings: Settings
) -> None:
    log_in_via_cas(page, live_server, "demo", "test")

    assert page.url == f"{live_server.url}/transfer/"

    # Logging out redirects the user to the CAS server logout page.
    click_logout_from_user_menu(page)
    assert page.url.startswith(f"{settings.CAS_SERVER_URL}logout")

    # The CAS single sign-on session is over, so authenticating again
    # requires to submit the CAS login form.
    page.goto(live_server.url)
    assert page.url.startswith(f"{settings.CAS_SERVER_URL}login")
    expect(page.locator("#username")).to_be_visible()
