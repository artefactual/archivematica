import pytest
import pytest_django
from django.contrib.auth.models import User
from tastypie.models import ApiKey

from archivematica.dashboard.components.accounts.backends import CustomLDAPBackend
from archivematica.dashboard.components.accounts.backends import (
    CustomShibbolethRemoteUserBackend,
)


@pytest.mark.parametrize(
    "ldap_username,expected",
    [
        ("demo@example.com", "demo"),
        # Characters that the username shares with the suffix must survive.
        ("paula@example.com", "paula"),
    ],
)
def test_ldap_backend_removes_exact_username_suffix(
    settings: pytest_django.Settings, ldap_username: str, expected: str
) -> None:
    settings.AUTH_LDAP_USERNAME_SUFFIX = "@example.com"

    assert CustomLDAPBackend().ldap_to_django_username(ldap_username) == expected


def test_ldap_backend_appends_username_suffix(
    settings: pytest_django.Settings,
) -> None:
    settings.AUTH_LDAP_USERNAME_SUFFIX = "@example.com"

    assert CustomLDAPBackend().django_to_ldap_username("demo") == "demo@example.com"


SHIBBOLETH_ATTRIBUTES = {
    "first_name": "Demo",
    "last_name": "User",
    "email": "demo@example.com",
    "entitlement": "preservation-user",
}


@pytest.mark.django_db
def test_shibboleth_backend_creates_user_with_attributes_and_api_key() -> None:
    user = CustomShibbolethRemoteUserBackend().authenticate(
        None, remote_user="demo@example.com", shib_meta=SHIBBOLETH_ATTRIBUTES
    )

    assert user is not None
    assert user.username == "demo@example.com"
    assert (user.first_name, user.last_name, user.email) == (
        "Demo",
        "User",
        "demo@example.com",
    )
    assert not user.has_usable_password()
    assert ApiKey.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_shibboleth_backend_updates_existing_user_attributes(
    django_user_model: type[User],
) -> None:
    existing = django_user_model.objects.create(
        username="demo@example.com", first_name="Old", email="old@example.com"
    )

    user = CustomShibbolethRemoteUserBackend().authenticate(
        None, remote_user="demo@example.com", shib_meta=SHIBBOLETH_ATTRIBUTES
    )

    assert user is not None
    assert user.pk == existing.pk
    assert (user.first_name, user.email) == ("Demo", "demo@example.com")


@pytest.mark.django_db
def test_shibboleth_backend_rejects_inactive_user(
    django_user_model: type[User],
) -> None:
    django_user_model.objects.create(username="demo@example.com", is_active=False)

    assert (
        CustomShibbolethRemoteUserBackend().authenticate(
            None, remote_user="demo@example.com", shib_meta=SHIBBOLETH_ATTRIBUTES
        )
        is None
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "django-shibboleth-remoteuser fails with ValueError (min() of an empty "
        "list) when no attribute that maps to a user field is released"
    ),
)
@pytest.mark.django_db
def test_shibboleth_backend_accepts_login_without_user_field_attributes() -> None:
    user = CustomShibbolethRemoteUserBackend().authenticate(
        None,
        remote_user="demo@example.com",
        shib_meta={"entitlement": "preservation-user"},
    )

    assert user is not None
    assert user.username == "demo@example.com"
