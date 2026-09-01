import pytest
import pytest_django

from archivematica.dashboard.components.accounts.backends import CustomLDAPBackend


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
