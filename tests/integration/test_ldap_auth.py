import os
import re
import uuid
from collections.abc import Callable

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django.live_server_helper import LiveServer
from tastypie.models import ApiKey

ClickAndWaitFor = Callable[
    [Page, Locator | Callable[[], None], str | re.Pattern[str] | Locator], None
]

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)

if not django_settings.LDAP_AUTHENTICATION:
    pytest.skip("Skipping LDAP integration tests", allow_module_level=True)


def fill_ldap_login(
    page: Page, live_server: LiveServer, username: str, password: str = "test"
) -> Locator:
    page.goto(live_server.url)
    page.get_by_label("Username").fill(
        f"{username}{django_settings.AUTH_LDAP_USERNAME_SUFFIX}"
    )
    page.get_by_label("Password").fill(password)
    return page.get_by_role("button", name="Log in")


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


def get_profile_details(
    page: Page, live_server: LiveServer, click_and_wait_for: ClickAndWaitFor
) -> list[str]:
    click_and_wait_for(
        page,
        lambda: click_profile_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:profile')}",
    )
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None

    return [item.strip() for item in details_text.splitlines() if item.strip()]


@pytest.mark.django_db
def test_ldap_backend_creates_local_user_and_maps_profile_attributes(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    click_and_wait_for(
        page, fill_ldap_login(page, live_server, "demo"), f"{live_server.url}/transfer/"
    )
    assert get_profile_details(page, live_server, click_and_wait_for) == [
        "Username",
        "demo",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]

    user = django_user_model.objects.get(username="demo")
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser
    assert ApiKey.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_ldap_backend_updates_existing_user_attributes(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    user = django_user_model.objects.create(
        username="manager",
        first_name="Outdated",
        last_name="Profile",
        email="old@example.com",
    )

    click_and_wait_for(
        page,
        fill_ldap_login(page, live_server, "manager"),
        f"{live_server.url}/transfer/",
    )
    user.refresh_from_db()
    assert (user.first_name, user.last_name, user.email) == (
        "Manager",
        "User",
        "manager@example.com",
    )
    assert django_user_model.objects.filter(username="manager").count() == 1


@pytest.mark.django_db
def test_ldap_backend_maps_username_suffix_end_to_end(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    click_and_wait_for(
        page,
        fill_ldap_login(page, live_server, "suffix"),
        f"{live_server.url}/transfer/",
    )
    assert django_user_model.objects.filter(username="suffix").exists()
    assert not django_user_model.objects.filter(username="suffix_ldap").exists()


@pytest.mark.django_db
def test_administrator_group_maps_django_flags(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    # The fixture puts admin in every role group. Administrator flags must win.
    click_and_wait_for(
        page,
        fill_ldap_login(page, live_server, "admin"),
        f"{live_server.url}/transfer/",
    )
    assert get_profile_details(page, live_server, click_and_wait_for) == [
        "Username",
        "admin",
        "Name",
        "Admin User",
        "E-mail",
        "admin@example.com",
        "Admin",
        "yes",
    ]

    user = django_user_model.objects.get(username="admin")
    assert user.is_active
    assert user.is_staff
    assert user.is_superuser


@pytest.mark.parametrize("username", ["disabled", "outsider"])
@pytest.mark.django_db
def test_required_and_denied_groups_reject_login(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    username: str,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    click_and_wait_for(
        page, fill_ldap_login(page, live_server, username), page.locator("div.alert")
    )

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")
    expect(page.locator("div.alert")).to_contain_text(
        "Please enter a correct username and password"
    )
    assert not django_user_model.objects.filter(username=username).exists()


@pytest.mark.django_db
def test_wrong_password_is_rejected(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    click_and_wait_for(
        page,
        fill_ldap_login(page, live_server, "demo", "wrong-password"),
        page.locator("div.alert"),
    )

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")
    expect(page.locator("div.alert")).to_contain_text(
        "Please enter a correct username and password"
    )
    assert not django_user_model.objects.filter(username="demo").exists()


@pytest.mark.django_db
def test_logout_ends_local_ldap_session(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    click_and_wait_for(
        page, fill_ldap_login(page, live_server, "demo"), f"{live_server.url}/transfer/"
    )
    click_and_wait_for(
        page,
        lambda: click_logout_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:login')}",
    )
