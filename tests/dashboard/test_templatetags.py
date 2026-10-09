import pytest
from django.contrib.auth.models import User
from tastypie.models import ApiKey

from archivematica.dashboard.main.templatetags.user import api_key
from archivematica.dashboard.main.templatetags.user import logout_link


@pytest.mark.django_db
def test_api_key_shows_message_when_no_api_key(admin_user: User) -> None:
    assert api_key(admin_user) == "<no API key generated>"


@pytest.mark.django_db
def test_api_key_shows_api_key_when_set(admin_user: User) -> None:
    ApiKey.objects.create(user=admin_user, key="my-api-key")

    assert api_key(admin_user) == "my-api-key"


def test_logout_link_uses_logout_link_from_context_when_available() -> None:
    assert logout_link({"logout_link": "/shibboleth/logout"}) == "/shibboleth/logout"


def test_logout_link_uses_django_logout_when_logout_link_not_set() -> None:
    assert logout_link({}) == "/administration/accounts/logout/"
