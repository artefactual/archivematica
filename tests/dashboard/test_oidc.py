import base64
import json
from typing import Any

import jwt
import pytest
import pytest_django
from django.contrib.auth.models import User

from archivematica.dashboard.components.accounts.backends import CustomOIDCBackend


def _unsigned_jwt(payload: dict[str, object]) -> str:
    header: dict[str, object] = {"typ": "JWT", "alg": "none"}

    def encode(segment: dict[str, object]) -> str:
        encoded = base64.urlsafe_b64encode(json.dumps(segment).encode()).rstrip(b"=")
        return encoded.decode()

    return f"{encode(header)}.{encode(payload)}."


@pytest.fixture
def settings(settings: pytest_django.Settings) -> pytest_django.Settings:
    settings.OIDC_OP_TOKEN_ENDPOINT = "https://example.com/token"
    settings.OIDC_OP_USER_ENDPOINT = "https://example.com/user"
    settings.OIDC_OP_JWKS_ENDPOINT = "https://example.com/jwks"
    settings.OIDC_RP_CLIENT_ID = "rp_client_id"
    settings.OIDC_RP_CLIENT_SECRET = "rp_client_secret"
    settings.OIDC_RP_SIGN_ALGO = "RS256"
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


def _set_verified_access_claims(
    monkeypatch: pytest.MonkeyPatch, claims: dict[str, object]
) -> None:
    monkeypatch.setattr(
        CustomOIDCBackend,
        "verify_access_token",
        lambda self, access_token, verified_id: claims,
    )


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
def test_get_userinfo(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Encoded at https://www.jsonwebtoken.io/
    # {"email": "test@example.com"}
    id_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJqdGkiOiI1M2QyMzUzMy04NDk0LTQyZWQtYTJiZC03Mzc2MjNmMjUzZjciLCJpYXQiOjE1NzMwMzE4NDQsImV4cCI6MTU3MzAzNTQ0NH0.m3nHgvj_DyVJMcW5eyYuUss1Y0PNzJV2O3bX0b_DCmI"
    # {"given_name": "Test", "family_name": "User"}
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnaXZlbl9uYW1lIjoiVGVzdCIsImZhbWlseV9uYW1lIjoiVXNlciIsImp0aSI6ImRhZjIwNTNiLWE4MTgtNDE1Yy1hM2Y1LTkxYWVhMTMxYjljZCIsImlhdCI6MTU3MzAzMTk3OSwiZXhwIjoxNTczMDM1NTc5fQ.cGcmt7d9IuKndvrqPpAH3Dvb3KyCOMqixUWgS7sg8r4"
    backend = CustomOIDCBackend()
    _set_verified_access_claims(
        monkeypatch, {"given_name": "Test", "family_name": "User"}
    )

    info = backend.get_userinfo(
        access_token=access_token,
        id_token=id_token,
        verified_id={"email": "test@example.com", "iss": "https://example.com"},
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
        lambda access_token, id_token, verified_id: {"email": "new@example.com"},
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
        lambda access_token, id_token, verified_id: {"email": "existing@example.com"},
    )

    user = backend.get_or_create_user(
        access_token="access-token",
        id_token="id-token",
        payload={"sub": "test"},
    )

    assert user == existing_user
    assert User.objects.count() == 1


def test_get_userinfo_uses_verified_id_claims_for_id_token_attributes(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    id_token = _unsigned_jwt({"email": "forged@example.com"})
    access_token = _unsigned_jwt(
        {"given_name": "Test", "family_name": "User", "realm_access": {}}
    )
    backend = CustomOIDCBackend()
    _set_verified_access_claims(
        monkeypatch, {"given_name": "Test", "family_name": "User"}
    )

    info = backend.get_userinfo(
        access_token=access_token,
        id_token=id_token,
        verified_id={"email": "verified@example.com", "iss": "https://example.com"},
    )

    assert info["email"] == "verified@example.com"


def test_get_userinfo_does_not_require_raw_id_token_to_be_decodable_after_verification(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    access_token = _unsigned_jwt({"given_name": "Test", "family_name": "User"})
    backend = CustomOIDCBackend()
    _set_verified_access_claims(
        monkeypatch, {"given_name": "Test", "family_name": "User"}
    )

    info = backend.get_userinfo(
        access_token=access_token,
        id_token="not-a-jwt",
        verified_id={"email": "verified@example.com", "iss": "https://example.com"},
    )

    assert info["email"] == "verified@example.com"
    assert info["first_name"] == "Test"
    assert info["last_name"] == "User"


def test_get_userinfo_does_not_accept_unverified_access_token_claims(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    id_token = _unsigned_jwt({"email": "forged@example.com"})
    access_token = _unsigned_jwt(
        {
            "given_name": "Forged",
            "family_name": "User",
            "realm_access": {"roles": ["admin"]},
        }
    )
    backend = CustomOIDCBackend()

    def reject_access_token(
        self: CustomOIDCBackend, access_token: str, verified_id: dict[str, Any]
    ) -> dict[str, Any]:
        raise jwt.InvalidSignatureError("Invalid access token signature.")

    monkeypatch.setattr(
        CustomOIDCBackend,
        "verify_access_token",
        reject_access_token,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        backend.get_userinfo(
            access_token=access_token,
            id_token=id_token,
            verified_id={"email": "verified@example.com", "iss": "https://example.com"},
        )


def test_verify_access_token_validates_signature_issuer_expiry_algorithm_and_audience(
    settings: pytest_django.Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = CustomOIDCBackend()
    decode_kwargs: dict[str, Any] = {}

    class SigningKey:
        key = "signing-key"

    class JWKClient:
        def __init__(self, jwks_endpoint: str) -> None:
            decode_kwargs["jwks_endpoint"] = jwks_endpoint

        def get_signing_key_from_jwt(self, access_token: str) -> SigningKey:
            decode_kwargs["signing_key_token"] = access_token
            return SigningKey()

    def decode(
        token: str,
        key: Any,
        algorithms: list[str],
        issuer: str,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        decode_kwargs.update(
            {
                "token": token,
                "key": key,
                "algorithms": algorithms,
                "issuer": issuer,
                "options": options,
            }
        )
        return {
            "aud": ["rp_client_id"],
            "exp": 1573035579,
            "given_name": "Test",
        }

    monkeypatch.setattr(
        "archivematica.dashboard.components.accounts.backends.PyJWKClient", JWKClient
    )
    monkeypatch.setattr(
        "archivematica.dashboard.components.accounts.backends.jwt.decode", decode
    )

    payload = backend.verify_access_token(
        "access-token", {"iss": "https://example.com/issuer"}
    )

    assert payload["given_name"] == "Test"
    assert decode_kwargs == {
        "jwks_endpoint": "https://example.com/jwks",
        "signing_key_token": "access-token",
        "token": "access-token",
        "key": "signing-key",
        "algorithms": ["RS256"],
        "issuer": "https://example.com/issuer",
        "options": {"verify_aud": False},
    }


def test_verify_access_token_rejects_missing_issuer(
    settings: pytest_django.Settings,
) -> None:
    backend = CustomOIDCBackend()

    with pytest.raises(jwt.InvalidIssuerError):
        backend.verify_access_token("access-token", {})


def test_verify_access_token_accepts_keycloak_authorized_party(
    settings: pytest_django.Settings,
) -> None:
    backend = CustomOIDCBackend()

    backend.verify_access_token_audience({"aud": ["account"], "azp": "rp_client_id"})


def test_verify_access_token_rejects_wrong_audience(
    settings: pytest_django.Settings,
) -> None:
    backend = CustomOIDCBackend()

    with pytest.raises(jwt.InvalidAudienceError):
        backend.verify_access_token_audience({"aud": ["other"], "azp": "other"})
