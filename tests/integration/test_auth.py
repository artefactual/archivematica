import os
import uuid

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from playwright.sync_api import Page
from pytest_django.live_server_helper import LiveServer

if "RUN_INTEGRATION_TESTS" not in os.environ:
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.mark.django_db
def test_logout_link_logs_out_user(
    page: Page, live_server: LiveServer, dashboard_uuid: uuid.UUID, user: AbstractUser
) -> None:
    page.goto(live_server.url)
    assert page.url == f"{live_server.url}{reverse('accounts:login')}"

    page.get_by_label("Username").fill("foobar")
    page.get_by_label("Password").fill("foobar1A,")
    page.get_by_text("Log in", exact=True).click()

    assert page.url == f"{live_server.url}/transfer/"

    page.get_by_text("foobar").click()
    page.get_by_role("button", name="Log out").click()

    assert page.url == f"{live_server.url}{reverse('accounts:login')}"
