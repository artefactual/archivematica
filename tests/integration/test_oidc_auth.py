import os
import re
import uuid
from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django import Settings
from pytest_django.live_server_helper import LiveServer

ClickAndWaitFor = Callable[
    [Page, Locator | Callable[[], None], str | re.Pattern[str] | Locator], None
]

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)


def url_starting_with(prefix: str) -> re.Pattern[str]:
    return re.compile(f"^{re.escape(prefix)}")


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


@pytest.mark.django_db
def test_oidc_backend_creates_local_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(live_server.url)

    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        page.get_by_label("Username or email"),
    )
    page.get_by_label("Username or email").fill("demo@example.com")
    page.get_by_label("Password", exact=True).fill("demo")
    click_and_wait_for(
        page, page.get_by_role("button", name="Sign In"), f"{live_server.url}/transfer/"
    )
    click_and_wait_for(
        page,
        lambda: click_profile_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:profile')}",
    )
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None
    assert [i.strip() for i in details_text.splitlines() if i.strip()] == [
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
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    user: User,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    click_and_wait_for(
        page, page.get_by_text("Log in", exact=True), f"{live_server.url}/transfer/"
    )

    click_and_wait_for(
        page,
        lambda: click_profile_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:profile')}",
    )
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None
    assert [i.strip() for i in details_text.splitlines() if i.strip()] == [
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
    dashboard_uuid: uuid.UUID,
    user: User,
    settings: Settings,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    disabled_backends = ["django.contrib.auth.backends.ModelBackend"]
    settings.AUTHENTICATION_BACKENDS = [
        b for b in settings.AUTHENTICATION_BACKENDS if b not in disabled_backends
    ]

    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    click_and_wait_for(
        page, page.get_by_text("Log in", exact=True), page.locator("div.alert")
    )
    expect(page).to_have_url(f"{live_server.url}{settings.LOGIN_URL}")
    error_text = page.locator("div.alert").text_content()
    assert error_text is not None
    assert "Please enter a correct username and password" in error_text.strip()


@pytest.mark.django_db
def test_setting_login_url_redirects_to_oidc_login_page(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    user: User,
    settings: Settings,
) -> None:
    page.goto(live_server.url)
    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")

    settings.LOGIN_URL = reverse("oidc_authentication_init")

    page.goto(live_server.url)

    expect(page).to_have_url(url_starting_with(settings.OIDC_OP_AUTHORIZATION_ENDPOINT))


@pytest.mark.django_db
def test_setting_request_parameter_in_local_login_url_redirects_to_secondary_provider_admin_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    settings: Settings,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        page.get_by_label("Username or email"),
    )
    page.get_by_label("Username or email").fill("supportadmin@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    click_and_wait_for(
        page, page.get_by_role("button", name="Sign In"), f"{live_server.url}/transfer/"
    )
    click_and_wait_for(
        page,
        lambda: click_profile_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:profile')}",
    )


@pytest.mark.django_db
def test_setting_request_parameter_in_local_login_url_redirects_to_secondary_provider_default_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    user: User,
    settings: Settings,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        page.get_by_label("Username or email"),
    )
    page.get_by_label("Username or email").fill("supportdefault@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    click_and_wait_for(
        page, page.get_by_role("button", name="Sign In"), f"{live_server.url}/transfer/"
    )

    click_and_wait_for(
        page,
        lambda: click_profile_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:profile')}",
    )
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None
    assert [i.strip() for i in details_text.splitlines() if i.strip()] == [
        "Username",
        "supportdefault@example.com",
        "Name",
        "SupportDefault User",
        "E-mail",
        "supportdefault@example.com",
        "Admin",
        "no",
    ]


@pytest.mark.django_db
def test_logging_out_logs_out_user_from_secondary_provider_admin_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    settings: Settings,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        page.get_by_label("Username or email"),
    )
    page.get_by_label("Username or email").fill("supportadmin@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    click_and_wait_for(
        page, page.get_by_role("button", name="Sign In"), f"{live_server.url}/transfer/"
    )

    # Logging out redirects the user to the login url.
    click_and_wait_for(
        page,
        lambda: click_logout_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:login')}",
    )

    # Logging in through the OIDC provider requires to authenticate again.
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )
    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        url_starting_with(
            settings.OIDC_PROVIDERS["SECONDARY"]["OIDC_OP_AUTHORIZATION_ENDPOINT"]
        ),
    )


@pytest.mark.django_db
def test_logging_out_logs_out_user_from_secondary_provider_default_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    settings: Settings,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        page.get_by_label("Username or email"),
    )
    page.get_by_label("Username or email").fill("supportdefault@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    click_and_wait_for(
        page, page.get_by_role("button", name="Sign In"), f"{live_server.url}/transfer/"
    )

    # Logging out redirects the user to the login url.
    click_and_wait_for(
        page,
        lambda: click_logout_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:login')}",
    )

    # Logging in through the OIDC provider requires to authenticate again.
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )
    click_and_wait_for(
        page,
        page.get_by_role("link", name="Log in with OpenID Connect"),
        url_starting_with(
            settings.OIDC_PROVIDERS["SECONDARY"]["OIDC_OP_AUTHORIZATION_ENDPOINT"]
        ),
    )
