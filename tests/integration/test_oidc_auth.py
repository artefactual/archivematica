import os
import re
import uuid

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django import Settings
from pytest_django.live_server_helper import LiveServer

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
) -> None:
    page.goto(live_server.url)

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("demo@example.com")
    page.get_by_label("Password", exact=True).fill("demo")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    click_profile_from_user_menu(page)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:profile')}")
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
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID, user: User
) -> None:
    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_text("Log in", exact=True).click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")

    click_profile_from_user_menu(page)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:profile')}")
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
) -> None:
    disabled_backends = ["django.contrib.auth.backends.ModelBackend"]
    settings.AUTHENTICATION_BACKENDS = [
        b for b in settings.AUTHENTICATION_BACKENDS if b not in disabled_backends
    ]

    page.goto(live_server.url)

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_text("Log in", exact=True).click()

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
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("supportadmin@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    click_profile_from_user_menu(page)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:profile')}")


@pytest.mark.django_db
def test_setting_request_parameter_in_local_login_url_redirects_to_secondary_provider_default_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    user: User,
    settings: Settings,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("supportdefault@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")

    click_profile_from_user_menu(page)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:profile')}")
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
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("supportadmin@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")

    # Logging out redirects the user to the login url.
    click_logout_from_user_menu(page)
    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")

    # Logging in through the OIDC provider requires to authenticate again.
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )
    page.get_by_role("link", name="Log in with OpenID Connect").click()
    expect(page).to_have_url(
        url_starting_with(
            settings.OIDC_PROVIDERS["SECONDARY"]["OIDC_OP_AUTHORIZATION_ENDPOINT"]
        )
    )


@pytest.mark.django_db
def test_logging_out_logs_out_user_from_secondary_provider_default_role(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    settings: Settings,
) -> None:
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )

    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill("supportdefault@example.com")
    page.get_by_label("Password", exact=True).fill("support")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")

    # Logging out redirects the user to the login url.
    click_logout_from_user_menu(page)
    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")

    # Logging in through the OIDC provider requires to authenticate again.
    page.goto(
        f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"
    )
    page.get_by_role("link", name="Log in with OpenID Connect").click()
    expect(page).to_have_url(
        url_starting_with(
            settings.OIDC_PROVIDERS["SECONDARY"]["OIDC_OP_AUTHORIZATION_ENDPOINT"]
        )
    )


def log_in_with_openid_connect(page: Page, username: str, password: str) -> None:
    page.get_by_role("link", name="Log in with OpenID Connect").click()
    page.get_by_label("Username or email").fill(username)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign In").click()


def secondary_provider_login_url(live_server: LiveServer, settings: Settings) -> str:
    return f"{live_server.url}{reverse('accounts:login')}?{settings.OIDC_PROVIDER_QUERY_PARAM_NAME}=SECONDARY"


def set_secondary_provider_setting(
    settings: Settings, name: str, value: object
) -> None:
    """Give the secondary provider a setting of its own.

    The providers are replaced as a whole so that the settings fixture restores
    them after the test.
    """
    settings.OIDC_PROVIDERS = {
        **settings.OIDC_PROVIDERS,
        "SECONDARY": {**settings.OIDC_PROVIDERS["SECONDARY"], name: value},
    }


@pytest.mark.django_db
def test_oidc_backend_does_not_create_local_user_when_creation_is_disabled(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    settings.OIDC_CREATE_USER = False

    page.goto(live_server.url)
    log_in_with_openid_connect(page, "demo@example.com", "demo")

    # The login fails and the browser ends up on the login page again.
    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")
    assert not django_user_model.objects.filter(username="demo@example.com").exists()


@pytest.mark.django_db
def test_oidc_backend_authenticates_existing_user_when_creation_is_disabled(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    settings.OIDC_CREATE_USER = False
    django_user_model.objects.create_user(
        username="demo@example.com",
        email="demo@example.com",
        first_name="Demo",
        last_name="User",
    )

    page.goto(live_server.url)
    log_in_with_openid_connect(page, "demo@example.com", "demo")

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    assert django_user_model.objects.filter(username="demo@example.com").count() == 1


@pytest.mark.django_db
def test_secondary_provider_follows_the_global_create_user_setting(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    settings.OIDC_CREATE_USER = False

    page.goto(secondary_provider_login_url(live_server, settings))
    log_in_with_openid_connect(page, "supportdefault@example.com", "support")

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")
    assert not django_user_model.objects.filter(
        username="supportdefault@example.com"
    ).exists()


@pytest.mark.django_db
def test_secondary_provider_create_user_setting_overrides_the_global_one(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    settings.OIDC_CREATE_USER = False
    set_secondary_provider_setting(settings, "OIDC_CREATE_USER", True)

    page.goto(secondary_provider_login_url(live_server, settings))
    log_in_with_openid_connect(page, "supportdefault@example.com", "support")

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    assert (
        django_user_model.objects.filter(
            username="supportdefault@example.com",
            first_name="SupportDefault",
            last_name="User",
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_secondary_provider_can_disable_user_creation_on_its_own(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
    settings: Settings,
) -> None:
    set_secondary_provider_setting(settings, "OIDC_CREATE_USER", False)

    page.goto(secondary_provider_login_url(live_server, settings))
    log_in_with_openid_connect(page, "supportdefault@example.com", "support")

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")
    assert not django_user_model.objects.filter(
        username="supportdefault@example.com"
    ).exists()
