import re
from collections.abc import Callable

import pytest
from django.contrib.auth.models import AbstractUser
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import expect

# A locator to click, or a zero-argument callable that performs the click.
ClickTarget = Locator | Callable[[], None]
# What the click must produce: a page URL, or an element that becomes visible.
ClickResult = str | re.Pattern[str] | Locator
ClickAndWaitFor = Callable[[Page, ClickTarget, ClickResult], None]


@pytest.fixture
def user(django_user_model: type[AbstractUser]) -> AbstractUser:
    user = django_user_model.objects.create(
        username="foobar",
        email="foobar@example.com",
        first_name="Foo",
        last_name="Bar",
    )
    user.set_password("foobar1A,")
    user.save()

    return user


@pytest.fixture
def click_and_wait_for() -> ClickAndWaitFor:
    """Click and wait for ``until``, clicking once more if nothing happened at all.

    Firefox occasionally drops a synthesized click while a page is still
    settling (see the traces uploaded by the authentication workflows). A click
    that reached the page is not repeated, because it returns only once the
    navigation it triggered has committed, so the URL has already changed
    before the grace period starts. Where the expected result is an element on
    the same URL the guard cannot tell the two apart and the click is repeated,
    which those sites tolerate. Menu items must be given as a callable that
    also reopens the menu, since a lost click closes it.
    """
    grace_ms = 2000
    timeout_ms = 5000

    def click(target: ClickTarget) -> None:
        if callable(target):
            target()
        else:
            target.click()

    def reached(page: Page, until: ClickResult, timeout: int) -> None:
        if isinstance(until, Locator):
            expect(until).to_be_visible(timeout=timeout)
        else:
            expect(page).to_have_url(until, timeout=timeout)

    def click_and_wait(page: Page, target: ClickTarget, until: ClickResult) -> None:
        origin = page.url
        click(target)
        try:
            reached(page, until, grace_ms)
        except AssertionError:
            if page.url == origin:
                click(target)
            reached(page, until, timeout_ms)

    return click_and_wait
