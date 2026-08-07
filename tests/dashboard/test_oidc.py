import pytest
import pytest_django
from django.contrib.auth.models import User

from archivematica.dashboard.components.accounts.backends import CustomOIDCBackend


@pytest.fixture
def settings(settings: pytest_django.Settings) -> pytest_django.Settings:
    settings.OIDC_OP_TOKEN_ENDPOINT = "https://example.com/token"
    settings.OIDC_OP_USER_ENDPOINT = "https://example.com/user"
    settings.OIDC_RP_CLIENT_ID = "rp_client_id"
    settings.OIDC_RP_CLIENT_SECRET = "rp_client_secret"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    settings.DEFAULT_OIDC_CLAIMS = {
        "given_name": "first_name",
        "family_name": "last_name",
    }
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = False
    settings.OIDC_CREATE_USER = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ID_ATTRIBUTE_MAP = {"email": "email"}
    settings.OIDC_USERNAME_ALGO = lambda email: email

    return settings


@pytest.mark.django_db
def test_create_user(settings: pytest_django.Settings) -> None:
    """
    Test that the user is created with the correct attributes and that the API key is generated.
    User will not be superuser because the setting OIDC_OP_SET_ROLES_FROM_CLAIMS is False.
    """
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "realm_access": {"roles": ["admin"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert not user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_set_admin_from_claim(settings: pytest_django.Settings) -> None:
    """
    Test that the user is created with the correct attributes and that the API key is generated.
    User will be superuser because the setting OIDC_OP_SET_ROLES_FROM_CLAIMS is True
    and the role claim is set to "admin".
    """
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "realm_access": {"roles": ["admin"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_role_from_claims(settings: pytest_django.Settings) -> None:
    """
    The role given to a new user is based on token contents.
    In this test, we're ensuring that the highest-permission valid role
    found in the OIDC token claims is assigned.
    """
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "realm_access": {"roles": ["admin", "default"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_role_from_claims_reverese_token_role_order(
    settings: pytest_django.Settings,
) -> None:
    """
    The role given to a new user is based on token contents.
    In this test, we're ensuring that the highest-permission valid role
    found in the OIDC token claims is assigned.
    """
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "realm_access": {"roles": ["reader", "admin"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_set_admin_from_alternate_token_value(
    settings: pytest_django.Settings,
) -> None:
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    settings.OIDC_ROLE_CLAIM_ADMIN = "test"
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "realm_access": {"roles": ["test"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_failure_no_claims_in_token(
    settings: pytest_django.Settings,
) -> None:
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {"email": "test@example.com", "first_name": "Test", "last_name": "User"}
    )

    assert user is None


@pytest.mark.django_db
def test_create_user_set_admin_from_alt_claim_path(
    settings: pytest_django.Settings,
) -> None:
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "custom_claims.user_roles"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "custom_claims": {"user_roles": ["admin"]},
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_create_user_admin_from_claims_simple_role(
    settings: pytest_django.Settings,
) -> None:
    settings.OIDC_OP_SET_ROLES_FROM_CLAIMS = True
    settings.OIDC_OP_ROLE_CLAIM_PATH = "role"
    settings.OIDC_ACCESS_ATTRIBUTE_MAP = {
        "given_name": "first_name",
        "family_name": "last_name",
        "realm_access": "realm_access",
    }
    backend = CustomOIDCBackend()

    user = backend.create_user(
        {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "admin",
        }
    )

    assert user is not None
    user.refresh_from_db()
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert user.is_superuser
    assert user.api_key


@pytest.mark.django_db
def test_get_userinfo(settings: pytest_django.Settings) -> None:
    # Encoded at https://www.jsonwebtoken.io/
    # {"email": "test@example.com"}
    id_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJqdGkiOiI1M2QyMzUzMy04NDk0LTQyZWQtYTJiZC03Mzc2MjNmMjUzZjciLCJpYXQiOjE1NzMwMzE4NDQsImV4cCI6MTU3MzAzNTQ0NH0.m3nHgvj_DyVJMcW5eyYuUss1Y0PNzJV2O3bX0b_DCmI"
    # {"given_name": "Test", "family_name": "User"}
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnaXZlbl9uYW1lIjoiVGVzdCIsImZhbWlseV9uYW1lIjoiVXNlciIsImp0aSI6ImRhZjIwNTNiLWE4MTgtNDE1Yy1hM2Y1LTkxYWVhMTMxYjljZCIsImlhdCI6MTU3MzAzMTk3OSwiZXhwIjoxNTczMDM1NTc5fQ.cGcmt7d9IuKndvrqPpAH3Dvb3KyCOMqixUWgS7sg8r4"
    backend = CustomOIDCBackend()

    info = backend.get_userinfo(
        access_token=access_token, id_token=id_token, verified_id={}
    )

    assert info["email"] == "test@example.com"
    assert info["first_name"] == "Test"
    assert info["last_name"] == "User"


@pytest.mark.django_db
def test_get_or_create_user_does_not_create_user_when_disabled(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.OIDC_CREATE_USER = False
    backend = CustomOIDCBackend()
    monkeypatch.setattr(
        backend,
        "get_userinfo",
        lambda access_token, id_token, payload: {"email": "new@example.com"},
    )

    user = backend.get_or_create_user(
        access_token="access-token",
        id_token="id-token",
        payload={"sub": "test"},
    )

    assert user is None
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_get_or_create_user_returns_existing_user_when_creation_disabled(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.OIDC_CREATE_USER = False
    existing_user = User.objects.create_user(
        username="existing@example.com", email="existing@example.com"
    )
    backend = CustomOIDCBackend()
    monkeypatch.setattr(
        backend,
        "get_userinfo",
        lambda access_token, id_token, payload: {"email": "existing@example.com"},
    )

    user = backend.get_or_create_user(
        access_token="access-token",
        id_token="id-token",
        payload={"sub": "test"},
    )

    assert user == existing_user
    assert User.objects.count() == 1
