import os
import re
import uuid

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import Browser
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django.live_server_helper import LiveServer
from tastypie.models import ApiKey

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)

if not django_settings.SHIBBOLETH_AUTHENTICATION:
    pytest.skip("Skipping Shibboleth integration tests", allow_module_level=True)

# The Dashboard does not speak SAML: it trusts the request headers that a
# Shibboleth service provider in front of it sets. Most tests below play the
# service provider themselves by sending those headers to the live server. The
# last section drives a real SAML login through the shibboleth-sp service,
# which authenticates against Keycloak and proxies to the live server.
SP_URL = os.environ.get("SHIBBOLETH_SP_URL", "http://shibboleth-sp")

LOGOUT_TARGET = "/administration/accounts/logged-out"


def shibboleth_headers(
    username: str = "demo",
    first_name: str = "Demo",
    entitlements: str = "preservation-user",
) -> dict[str, str]:
    """Headers mod_shib exports after a login, for the attributes the
    Dashboard maps: eppn, givenName, sn, mail and entitlement."""
    return {
        "eppn": f"{username}@example.com",
        "givenName": first_name,
        "sn": "User",
        "mail": f"{username}@example.com",
        "entitlement": entitlements,
    }


def url_starting_with(prefix: str) -> re.Pattern[str]:
    return re.compile(f"^{re.escape(prefix)}")


def open_user_menu(page: Page) -> None:
    user_menu = page.locator("li.user.dropdown")
    expect(user_menu).to_be_visible()
    user_menu.evaluate("node => node.classList.add('open')")


def get_profile_details(page: Page, base_url: str) -> list[str]:
    open_user_menu(page)
    page.get_by_role("link", name="Your profile").click()

    expect(page).to_have_url(f"{base_url}{reverse('accounts:profile')}")
    details_text = page.locator("dl.dl-horizontal").text_content()
    assert details_text is not None

    return [item.strip() for item in details_text.splitlines() if item.strip()]


def logout_form_action(page: Page) -> str | None:
    open_user_menu(page)
    return page.locator("li.user.dropdown form").get_attribute("action")


@pytest.mark.django_db
def test_headers_create_local_user_with_mapped_attributes(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    assert get_profile_details(page, live_server.url) == [
        "Username",
        "demo@example.com",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]
    user = django_user_model.objects.get(username="demo@example.com")
    assert not user.has_usable_password()
    assert ApiKey.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_headers_update_an_existing_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    existing = django_user_model.objects.create(
        username="demo@example.com", first_name="Old", email="old@example.com"
    )

    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)

    assert get_profile_details(page, live_server.url)[1:6] == [
        "demo@example.com",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
    ]
    assert django_user_model.objects.get(username="demo@example.com").pk == existing.pk


@pytest.mark.django_db
def test_headers_preserve_a_long_username(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    # The username is the principal name as released, however long.
    long_email = "person-with-very-long-name@long-institution-name.ac.uk"
    headers = shibboleth_headers()
    headers["eppn"] = headers["mail"] = long_email
    page.set_extra_http_headers(headers)
    page.goto(live_server.url)

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    assert get_profile_details(page, live_server.url)[:2] == [
        "Username",
        long_email,
    ]
    assert django_user_model.objects.filter(username=long_email).exists()


@pytest.mark.django_db
def test_entitlement_grants_and_revokes_superuser(
    browser: Browser,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    page = browser.new_page(
        extra_http_headers=shibboleth_headers(
            "admin",
            "Admin",
            "preservation-admin;preservation-manager;preservation-reviewer",
        )
    )
    page.goto(live_server.url)

    assert get_profile_details(page, live_server.url)[-1] == "yes"
    assert django_user_model.objects.get(username="admin@example.com").is_superuser
    page.context.close()

    # The flag is set on every authentication, so a new session without the
    # entitlement revokes it.
    page = browser.new_page(
        extra_http_headers=shibboleth_headers("admin", "Admin", "preservation-user")
    )
    page.goto(live_server.url)

    assert get_profile_details(page, live_server.url)[-1] == "no"
    assert not django_user_model.objects.get(username="admin@example.com").is_superuser
    page.context.close()


@pytest.mark.django_db
def test_attributes_are_only_read_when_a_session_is_established(
    browser: Browser, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    """Documents the library behaviour: once the user is logged in, changed
    headers are ignored until the user authenticates again."""
    page = browser.new_page(extra_http_headers=shibboleth_headers())
    page.goto(live_server.url)
    page.set_extra_http_headers(shibboleth_headers(first_name="Renamed"))
    page.goto(f"{live_server.url}{reverse('accounts:profile')}")

    assert "Demo User" in (page.locator("dl.dl-horizontal").text_content() or "")
    page.context.close()

    page = browser.new_page(extra_http_headers=shibboleth_headers(first_name="Renamed"))
    page.goto(f"{live_server.url}{reverse('accounts:profile')}")

    assert "Renamed User" in (page.locator("dl.dl-horizontal").text_content() or "")
    page.context.close()


@pytest.mark.django_db
def test_session_survives_requests_without_headers(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    """Documents the library behaviour: the local session is not ended when a
    request arrives without the remote user header."""
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)
    page.set_extra_http_headers({})
    page.goto(f"{live_server.url}/transfer/")

    expect(page).to_have_url(f"{live_server.url}/transfer/")
    expect(page.locator("li.user.dropdown")).to_be_visible()


@pytest.mark.django_db
def test_missing_entitlement_attribute_is_rejected(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    headers = shibboleth_headers()
    del headers["entitlement"]
    page.set_extra_http_headers(headers)

    response = page.goto(live_server.url)

    assert response is not None
    assert response.status == 500
    assert not django_user_model.objects.filter(username="demo@example.com").exists()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "django-shibboleth-remoteuser fails with ValueError (min() of an empty "
        "list) when no attribute that maps to a user field is released"
    ),
)
@pytest.mark.django_db
def test_login_with_only_eppn_and_entitlement(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(
        {"eppn": "demo@example.com", "entitlement": "preservation-user"}
    )
    page.goto(live_server.url)

    assert get_profile_details(page, live_server.url)[:2] == [
        "Username",
        "demo@example.com",
    ]


@pytest.mark.django_db
def test_without_headers_the_local_login_still_works(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID, user: User
) -> None:
    page.goto(live_server.url)

    expect(page).to_have_url(
        url_starting_with(f"{live_server.url}{reverse('accounts:login')}")
    )

    page.get_by_label("Username").fill(user.username)
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_role("button", name="Log in").click()

    expect(page).to_have_url(f"{live_server.url}/transfer/")


@pytest.mark.django_db
def test_inactive_user_is_not_logged_in(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    django_user_model.objects.create(username="demo@example.com", is_active=False)

    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)

    expect(page).to_have_url(
        url_starting_with(f"{live_server.url}{reverse('accounts:login')}")
    )


@pytest.mark.django_db
def test_logout_link_points_at_the_shibboleth_logout_view(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)

    assert (
        logout_form_action(page)
        == f"{reverse('shibboleth:logout')}?target={LOGOUT_TARGET}"
    )


@pytest.mark.django_db
def test_logout_ends_the_local_session_and_redirects_to_the_service_provider(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)

    # What the library's logout view implements: a GET. The redirect target
    # is served by the service provider, which then drops its own session, so
    # it is not followed here.
    response = page.request.get(
        f"{live_server.url}{reverse('shibboleth:logout')}?target={LOGOUT_TARGET}",
        headers=shibboleth_headers(),
        max_redirects=0,
    )

    assert response.status == 302
    assert (
        response.headers["location"] == f"/Shibboleth.sso/Logout?target={LOGOUT_TARGET}"
    )

    page.set_extra_http_headers({})
    page.goto(f"{live_server.url}/transfer/")

    expect(page).to_have_url(
        url_starting_with(f"{live_server.url}{reverse('accounts:login')}")
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "the logout form submits a POST, which the django-shibboleth-remoteuser "
        "logout view does not implement (405)"
    ),
)
@pytest.mark.django_db
def test_logout_button_logs_out(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)
    open_user_menu(page)

    page.get_by_role("button", name="Log out").click()

    assert page.url == f"{live_server.url}/Shibboleth.sso/Logout?target={LOGOUT_TARGET}"


@pytest.mark.django_db
def test_login_view_redirects_to_the_login_page(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    login_view = f"{live_server.url}{reverse('shibboleth:login')}?target=/transfer/"

    # Anonymous requests never reach the library's view: the Dashboard's
    # login-required middleware sends them to the login page first.
    page.goto(login_view)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")

    # Behind a service provider the request is authenticated, and the view
    # forwards the target to the login page.
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(login_view)

    expect(page).to_have_url(
        f"{live_server.url}{reverse('accounts:login')}?target=/transfer/"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SHIBBOLETH_LOGOUT_REDIRECT_URL points at a page whose view was removed "
        "(9318359ae); the accounts/logged_out.html template is not routed"
    ),
)
@pytest.mark.django_db
def test_logout_redirect_target_offers_the_shibboleth_login(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    response = page.goto(f"{live_server.url}{LOGOUT_TARGET}")

    assert response is not None
    assert response.status == 200

    page.get_by_role("link", name="Log in again").click()

    assert page.url == f"{live_server.url}{reverse('accounts:login')}?target="


@pytest.mark.django_db
def test_info_page_lists_the_mapped_attributes(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(f"{live_server.url}{reverse('shibboleth:info')}")

    text = page.locator("body").text_content() or ""
    for item in (
        "username: demo@example.com",
        "name: Demo User",
        "email: demo@example.com",
    ):
        assert item in text


@pytest.mark.django_db
def test_profile_page_disallows_edits(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(f"{live_server.url}{reverse('accounts:profile')}")

    for name in ("username", "first_name", "last_name", "email"):
        expect(page.locator(f"input[name={name}]")).to_have_count(0)
    expect(page.locator("input[name=regenerate_api_key]")).to_have_count(1)


@pytest.mark.django_db
def test_api_accepts_api_keys_and_session_calls_without_csrf_token(
    browser: Browser,
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    page.set_extra_http_headers(shibboleth_headers())
    page.goto(live_server.url)
    user = django_user_model.objects.get(username="demo@example.com")
    api_key = ApiKey.objects.get(user=user).key

    # API key authentication from a client with no session.
    context = browser.new_context()
    response = context.request.get(
        f"{live_server.url}/api/transfer/unapproved/",
        headers={"Authorization": f"ApiKey {user.username}:{api_key}"},
    )
    assert response.status == 200
    context.close()

    # Session authentication: with Shibboleth enabled the API does not enforce
    # CSRF, so a POST without a token reaches the endpoint, which then rejects
    # the empty form.
    response = page.request.post(
        f"{live_server.url}/api/transfer/approve/",
        form={"directory": ""},
        headers=shibboleth_headers(),
    )
    assert response.status == 500
    assert response.json()["message"] == "Please specify a transfer directory."


# Through the service provider.


def log_in_via_keycloak(page: Page, username: str, password: str = "test") -> None:
    page.get_by_label("Username or email").fill(username)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign In").click()
    # Keycloak posts the assertion to the service provider, which redirects
    # back into the application.
    expect(page).to_have_url(f"{SP_URL}/transfer/")


@pytest.mark.django_db
def test_saml_login_through_the_service_provider(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    page.goto(SP_URL)

    expect(page).to_have_url(
        url_starting_with("http://keycloak:8080/realms/shibboleth/")
    )

    log_in_via_keycloak(page, "demo")

    assert get_profile_details(page, SP_URL) == [
        "Username",
        "demo@example.com",
        "Name",
        "Demo User",
        "E-mail",
        "demo@example.com",
        "Admin",
        "no",
    ]
    assert not django_user_model.objects.get(
        username="demo@example.com"
    ).has_usable_password()

    page.goto(f"{SP_URL}/Shibboleth.sso/Session")
    session = page.locator("body").text_content() or ""
    for attribute in (
        "eppn: demo@example.com",
        "entitlement: preservation-user",
        "givenName: Demo",
        "sn: User",
        "mail: demo@example.com",
    ):
        assert attribute in session


@pytest.mark.django_db
def test_saml_admin_entitlement_grants_superuser(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    page.goto(SP_URL)
    log_in_via_keycloak(page, "admin")

    assert get_profile_details(page, SP_URL)[-1] == "yes"
    assert django_user_model.objects.get(username="admin@example.com").is_superuser


@pytest.mark.django_db
def test_saml_logout_ends_the_service_provider_session(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID
) -> None:
    page.goto(SP_URL)
    log_in_via_keycloak(page, "demo")

    page.goto(f"{SP_URL}{reverse('shibboleth:logout')}?target={LOGOUT_TARGET}")

    assert page.url == f"{SP_URL}/Shibboleth.sso/Logout?target={LOGOUT_TARGET}"
    assert "Logout completed successfully" in (
        page.locator("body").text_content() or ""
    )

    page.goto(f"{SP_URL}/Shibboleth.sso/Session")

    assert "A valid session was not found" in (
        page.locator("body").text_content() or ""
    )


@pytest.mark.django_db
def test_service_provider_rejects_spoofed_attribute_headers(
    browser: Browser,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    django_user_model: type[User],
) -> None:
    context = browser.new_context()
    spoofed = {"eppn": "attacker@example.com", "entitlement": "preservation-admin"}

    response = context.request.get(
        f"{SP_URL}/api/transfer/unapproved/", headers=spoofed
    )
    assert response.status == 500

    response = context.request.get(
        f"{SP_URL}/transfer/", headers=spoofed, max_redirects=0
    )
    assert response.status == 500

    assert not django_user_model.objects.filter(
        username="attacker@example.com"
    ).exists()
    context.close()


@pytest.mark.django_db
def test_service_provider_lets_api_key_requests_through(
    browser: Browser, live_server: LiveServer, dashboard_uuid: uuid.UUID, user: User
) -> None:
    api_key = ApiKey.objects.create(user=user)
    context = browser.new_context()

    response = context.request.get(
        f"{SP_URL}/api/transfer/unapproved/",
        headers={"Authorization": f"ApiKey {user.username}:{api_key.key}"},
    )
    assert response.status == 200

    # Without a key or a session the application, not the service provider,
    # answers.
    assert context.request.get(f"{SP_URL}/api/transfer/unapproved/").status == 403
    context.close()
