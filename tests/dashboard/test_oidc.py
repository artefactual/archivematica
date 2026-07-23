import time
from collections.abc import Mapping
from typing import Any

import jwt
import pytest
import pytest_django
import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from archivematica.dashboard.components.accounts.backends import CustomOIDCBackend


@pytest.fixture
def settings(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> pytest_django.fixtures.SettingsWrapper:
    settings.OIDC_OP_TOKEN_ENDPOINT = "https://example.com/token"
    settings.OIDC_OP_USER_ENDPOINT = "https://example.com/user"
    settings.OIDC_OP_ISSUER = "https://issuer.example"
    settings.OIDC_RP_CLIENT_ID = "rp_client_id"
    settings.OIDC_RP_CLIENT_SECRET = "rp_client_secret_that_is_long_enough"
    settings.OIDC_RP_SIGN_ALGO = "HS256"
    settings.OIDC_USE_NONCE = True
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
    settings.OIDC_OP_ROLE_CLAIM_PATH = "realm_access.roles"
    settings.OIDC_ID_ATTRIBUTE_MAP = {"email": "email"}
    settings.OIDC_USERNAME_ALGO = lambda email: email

    return settings


def valid_id_token_claims(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> dict[str, Any]:
    now = int(time.time())
    return {
        "iss": settings.OIDC_OP_ISSUER,
        "sub": "subject",
        "aud": settings.OIDC_RP_CLIENT_ID,
        "exp": now + 300,
        "iat": now,
        "nonce": "nonce",
        "email": "test@example.com",
    }


def encode_id_token(
    settings: pytest_django.fixtures.SettingsWrapper,
    claims: dict[str, Any],
) -> str:
    return jwt.encode(
        claims,
        settings.OIDC_RP_CLIENT_SECRET,
        algorithm=settings.OIDC_RP_SIGN_ALGO,
    )


@pytest.mark.django_db
def test_create_user(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
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
def test_create_user_set_admin_from_claim(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
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
def test_create_user_role_from_claims(
    settings: pytest_django.fixtures.SettingsWrapper,
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
    settings: pytest_django.fixtures.SettingsWrapper,
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
    settings: pytest_django.fixtures.SettingsWrapper,
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
    settings: pytest_django.fixtures.SettingsWrapper,
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
    settings: pytest_django.fixtures.SettingsWrapper,
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
    settings: pytest_django.fixtures.SettingsWrapper,
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


def test_verify_token_validates_id_token(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    claims = valid_id_token_claims(settings)
    backend = CustomOIDCBackend()

    result = backend.verify_token(
        encode_id_token(settings, claims),
        nonce="nonce",
    )

    assert result == claims


@pytest.mark.parametrize("missing_claim", ["iss", "sub", "aud", "exp", "iat"])
def test_verify_token_rejects_missing_required_id_token_claim(
    settings: pytest_django.fixtures.SettingsWrapper,
    missing_claim: str,
) -> None:
    claims = valid_id_token_claims(settings)
    del claims[missing_claim]
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match="missing required claims"):
        backend.verify_token(
            encode_id_token(settings, claims),
            nonce="nonce",
        )


@pytest.mark.parametrize(
    ("claim", "value", "message"),
    [
        ("iss", "https://attacker.example", "issuer"),
        ("sub", "", "subject"),
        ("aud", "another-client", "audience"),
        ("aud", [], "audience"),
        ("azp", "another-client", "authorized party"),
    ],
)
def test_verify_token_rejects_invalid_id_token_claim(
    settings: pytest_django.fixtures.SettingsWrapper,
    claim: str,
    value: object,
    message: str,
) -> None:
    claims = valid_id_token_claims(settings)
    claims[claim] = value
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match=message):
        backend.verify_token(
            encode_id_token(settings, claims),
            nonce="nonce",
        )


def test_verify_token_requires_authorized_party_for_multiple_audiences(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    claims = valid_id_token_claims(settings)
    claims["aud"] = [settings.OIDC_RP_CLIENT_ID, "another-client"]
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match="multiple audiences"):
        backend.verify_token(
            encode_id_token(settings, claims),
            nonce="nonce",
        )

    claims["azp"] = settings.OIDC_RP_CLIENT_ID
    result = backend.verify_token(
        encode_id_token(settings, claims),
        nonce="nonce",
    )

    assert result == claims


def test_verify_token_handles_expired_id_token(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    claims = valid_id_token_claims(settings)
    claims["exp"] = int(time.time()) - 1
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match="token verification failed"):
        backend.verify_token(
            encode_id_token(settings, claims),
            nonce="nonce",
        )


def test_verify_token_requires_expected_issuer(
    settings: pytest_django.fixtures.SettingsWrapper,
) -> None:
    claims = valid_id_token_claims(settings)
    settings.OIDC_OP_ISSUER = ""
    backend = CustomOIDCBackend()

    with pytest.raises(ImproperlyConfigured, match="OIDC_OP_ISSUER"):
        backend.verify_token(
            encode_id_token(settings, claims),
            nonce="nonce",
        )


def test_get_userinfo_uses_verified_claims(
    settings: pytest_django.fixtures.SettingsWrapper,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_tokens: dict[str, object] = {}

    def get_userinfo(
        backend: OIDCAuthenticationBackend,
        access_token: str,
        id_token: str,
        payload: Mapping[str, object] | None,
    ) -> dict[str, object]:
        requested_tokens["access_token"] = access_token
        requested_tokens["id_token"] = id_token
        requested_tokens["payload"] = payload
        return {
            "sub": "subject",
            "given_name": "Test",
            "family_name": "User",
            "realm_access": {"roles": ["default"]},
        }

    monkeypatch.setattr(OIDCAuthenticationBackend, "get_userinfo", get_userinfo)
    backend = CustomOIDCBackend()
    verified_id = {"sub": "subject", "email": "test@example.com"}

    info = backend.get_userinfo(
        access_token="opaque-access-token",
        id_token="untrusted-id-token",
        verified_id=verified_id,
    )

    assert requested_tokens == {
        "access_token": "opaque-access-token",
        "id_token": "untrusted-id-token",
        "payload": verified_id,
    }
    assert info["email"] == "test@example.com"
    assert info["first_name"] == "Test"
    assert info["last_name"] == "User"
    assert info["realm_access"] == {"roles": ["default"]}


@pytest.mark.parametrize("userinfo_subject", [None, "", "another-subject"])
def test_get_userinfo_rejects_subject_mismatch(
    settings: pytest_django.fixtures.SettingsWrapper,
    monkeypatch: pytest.MonkeyPatch,
    userinfo_subject: object,
) -> None:
    def get_userinfo(
        backend: OIDCAuthenticationBackend,
        access_token: str,
        id_token: str,
        payload: Mapping[str, object] | None,
    ) -> dict[str, object]:
        return {"sub": userinfo_subject}

    monkeypatch.setattr(OIDCAuthenticationBackend, "get_userinfo", get_userinfo)
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match="subject does not match"):
        backend.get_userinfo(
            access_token="opaque-access-token",
            id_token="untrusted-id-token",
            verified_id={"sub": "subject"},
        )


def test_get_userinfo_handles_provider_errors(
    settings: pytest_django.fixtures.SettingsWrapper,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def get_userinfo(
        backend: OIDCAuthenticationBackend,
        access_token: str,
        id_token: str,
        payload: Mapping[str, object] | None,
    ) -> dict[str, object]:
        raise requests.ConnectionError

    monkeypatch.setattr(OIDCAuthenticationBackend, "get_userinfo", get_userinfo)
    backend = CustomOIDCBackend()

    with pytest.raises(SuspiciousOperation, match="Unable to retrieve"):
        backend.get_userinfo(
            access_token="opaque-access-token",
            id_token="untrusted-id-token",
            verified_id={"sub": "subject"},
        )
