import os
import re
import uuid
from collections.abc import Callable

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import expect
from pytest_django.live_server_helper import LiveServer

ClickAndWaitFor = Callable[
    [Page, Locator | Callable[[], None], str | re.Pattern[str] | Locator], None
]

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)


def click_logout_from_user_menu(page: Page) -> None:
    user_menu = page.locator("li.user.dropdown")
    expect(user_menu).to_be_visible()
    user_menu.evaluate("node => node.classList.add('open')")
    page.get_by_role("button", name="Log out").click()


@pytest.mark.django_db
def test_logout_link_logs_out_user(
    page: Page,
    live_server: LiveServer,
    dashboard_uuid: uuid.UUID,
    user: AbstractUser,
    click_and_wait_for: ClickAndWaitFor,
) -> None:
    page.goto(live_server.url)

    expect(page).to_have_url(f"{live_server.url}{reverse('accounts:login')}")

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    click_and_wait_for(
        page, page.get_by_text("Log in", exact=True), f"{live_server.url}/transfer/"
    )

    click_and_wait_for(
        page,
        lambda: click_logout_from_user_menu(page),
        f"{live_server.url}{reverse('accounts:login')}",
    )
