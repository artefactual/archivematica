import base64
import hashlib
import hmac
from collections.abc import Mapping
from typing import Any
from typing import Optional

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django_auth_ldap.backend import LDAPBackend
from django_cas_ng.backends import CASBackend
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from shibboleth.backends import ShibbolethRemoteUserBackend

from archivematica.dashboard.components.helpers import generate_api_key


class CustomShibbolethRemoteUserBackend(ShibbolethRemoteUserBackend):
    def configure_user(self, user):
        generate_api_key(user)
        return user


class CustomCASBackend(CASBackend):
    def configure_user(self, user):
        generate_api_key(user)
        # If CAS_AUTOCONFIGURE_EMAIL and CAS_EMAIL_DOMAIN settings are
        # configured, add an email address for this user, using rule
        # username@domain.
        if settings.CAS_AUTOCONFIGURE_EMAIL and settings.CAS_EMAIL_DOMAIN:
            user.email = f"{user.username}@{settings.CAS_EMAIL_DOMAIN}"
            user.save()
        return user


class CustomLDAPBackend(LDAPBackend):
    """Append a usernamed suffix to LDAP users, if configured"""

    def ldap_to_django_username(self, username):
        return username.rstrip(settings.AUTH_LDAP_USERNAME_SUFFIX)

    def django_to_ldap_username(self, username):
        return username + settings.AUTH_LDAP_USERNAME_SUFFIX


class CustomOIDCBackend(OIDCAuthenticationBackend):
    """
    Provide OpenID Connect authentication
    """

    ID_TOKEN_REQUIRED_CLAIMS = frozenset({"iss", "sub", "aud", "exp", "iat"})
    ACCESS_TOKEN_REQUIRED_CLAIMS = frozenset({"iss", "sub", "exp", "iat"})

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Store additional settings as instance attributes.
        self.OIDC_OP_ISSUER = getattr(settings, "OIDC_OP_ISSUER", "")

        self.OIDC_OP_SET_ROLES_FROM_CLAIMS = getattr(
            settings, "OIDC_OP_SET_ROLES_FROM_CLAIMS", False
        )

        self.OIDC_OP_ROLE_CLAIM_PATH = getattr(
            settings, "OIDC_OP_ROLE_CLAIM_PATH", "realm_access.roles"
        )

        self.OIDC_ACCESS_ATTRIBUTE_MAP = getattr(
            settings, "OIDC_ACCESS_ATTRIBUTE_MAP", settings.DEFAULT_OIDC_CLAIMS
        )

        # Valid role claim name which may be extracted from OIDC token.
        self.OIDC_ROLE_CLAIM_ADMIN = getattr(settings, "OIDC_ROLE_CLAIM_ADMIN", "admin")
        self.OIDC_ROLE_CLAIM_DEFAULT = getattr(
            settings, "OIDC_ROLE_CLAIM_DEFAULT", "default"
        )
        # Valid user roles.
        self.USER_ROLE_ADMIN = "admin"
        self.USER_ROLE_DEFAULT = "default"

    def get_settings(self, attr: str, *args: Any) -> Any:
        if attr in [
            "OIDC_RP_CLIENT_ID",
            "OIDC_RP_CLIENT_SECRET",
            "OIDC_OP_AUTHORIZATION_ENDPOINT",
            "OIDC_OP_TOKEN_ENDPOINT",
            "OIDC_OP_USER_ENDPOINT",
            "OIDC_OP_JWKS_ENDPOINT",
            "OIDC_OP_LOGOUT_ENDPOINT",
            "OIDC_OP_ISSUER",
            "OIDC_OP_SET_ROLES_FROM_CLAIMS",
            "OIDC_OP_ROLE_CLAIM_PATH",
            "OIDC_ACCESS_ATTRIBUTE_MAP",
            "OIDC_ROLE_CLAIM_ADMIN",
            "OIDC_ROLE_CLAIM_DEFAULT",
        ]:
            # Retrieve the request object stored in the instance.
            request = getattr(self, "request", None)

            if request:
                provider_name = request.session.get("providername")

                if provider_name and provider_name in settings.OIDC_PROVIDERS:
                    provider_settings = settings.OIDC_PROVIDERS.get(provider_name, {})
                    value = provider_settings.get(attr)

                    if value is None:
                        raise ImproperlyConfigured(
                            f"Setting {attr} for provider {provider_name} not found"
                        )
                    return value

        # If request is None or provider_name session var is not set or attr is
        # not in the list, call the superclass's get_settings method.
        return OIDCAuthenticationBackend.get_settings(attr, *args)

    def authenticate(self, request: HttpRequest, **kwargs: Any) -> Any:
        self.request = request
        self.OIDC_RP_CLIENT_ID = self.get_settings("OIDC_RP_CLIENT_ID")
        self.OIDC_RP_CLIENT_SECRET = self.get_settings("OIDC_RP_CLIENT_SECRET")
        self.OIDC_OP_TOKEN_ENDPOINT = self.get_settings("OIDC_OP_TOKEN_ENDPOINT")
        self.OIDC_OP_USER_ENDPOINT = self.get_settings("OIDC_OP_USER_ENDPOINT")
        self.OIDC_OP_JWKS_ENDPOINT = self.get_settings("OIDC_OP_JWKS_ENDPOINT")
        self.OIDC_OP_ISSUER = self.get_settings("OIDC_OP_ISSUER")
        self.OIDC_OP_SET_ROLES_FROM_CLAIMS = self.get_settings(
            "OIDC_OP_SET_ROLES_FROM_CLAIMS"
        )
        self.OIDC_OP_ROLE_CLAIM_PATH = self.get_settings("OIDC_OP_ROLE_CLAIM_PATH")
        self.OIDC_ACCESS_ATTRIBUTE_MAP = self.get_settings("OIDC_ACCESS_ATTRIBUTE_MAP")
        self.OIDC_ROLE_CLAIM_ADMIN = self.get_settings("OIDC_ROLE_CLAIM_ADMIN")
        self.OIDC_ROLE_CLAIM_DEFAULT = self.get_settings("OIDC_ROLE_CLAIM_DEFAULT")

        return super().authenticate(request, **kwargs)

    def verify_token(self, token: str, **kwargs: Any) -> dict[str, Any]:
        """Verify a signed token and validate ID token claims."""
        try:
            claims = super().verify_token(token, **kwargs)
        except (
            jwt.PyJWTError,
            requests.RequestException,
            KeyError,
            ValueError,
        ) as exc:
            raise SuspiciousOperation("OIDC token verification failed.") from exc

        # The parent backend supplies the nonce keyword when verifying the ID
        # token. Only that path uses the ID token claim requirements.
        if "nonce" in kwargs:
            self.verify_id_token_claims(claims)

        return claims

    def verify_id_token_claims(self, claims: dict[str, Any]) -> None:
        """Validate claims that bind an ID token to this provider and client."""
        if not self.OIDC_OP_ISSUER:
            raise ImproperlyConfigured(
                "OIDC_OP_ISSUER must be configured to validate ID tokens"
            )

        missing_claims = self.ID_TOKEN_REQUIRED_CLAIMS.difference(claims)
        if missing_claims:
            missing = ", ".join(sorted(missing_claims))
            raise SuspiciousOperation(
                f"OIDC ID token is missing required claims: {missing}"
            )

        if claims["iss"] != self.OIDC_OP_ISSUER:
            raise SuspiciousOperation("OIDC ID token issuer does not match")

        if not isinstance(claims["sub"], str) or not claims["sub"]:
            raise SuspiciousOperation("OIDC ID token subject is invalid")

        audience_claim = claims["aud"]
        if isinstance(audience_claim, str):
            audiences = [audience_claim]
        elif isinstance(audience_claim, list) and all(
            isinstance(audience, str) for audience in audience_claim
        ):
            audiences = audience_claim
        else:
            raise SuspiciousOperation("OIDC ID token audience is invalid")

        if self.OIDC_RP_CLIENT_ID not in audiences:
            raise SuspiciousOperation("OIDC ID token audience does not match")

        authorized_party = claims.get("azp")
        if authorized_party is not None and authorized_party != self.OIDC_RP_CLIENT_ID:
            raise SuspiciousOperation("OIDC ID token authorized party does not match")

        if len(audiences) > 1 and authorized_party != self.OIDC_RP_CLIENT_ID:
            raise SuspiciousOperation(
                "OIDC ID token with multiple audiences has no valid authorized party"
            )

    def get_userinfo(
        self,
        access_token: str,
        id_token: str,
        verified_id: Mapping[str, object] | None,
    ) -> dict[str, Any]:
        """Extract user details from verified OIDC token claims."""
        if verified_id is None:
            raise SuspiciousOperation("OIDC ID token claims are missing")

        access_info = self.verify_access_token(access_token, verified_id)

        info: dict[str, Any] = {}

        for oidc_attr, user_attr in self.OIDC_ACCESS_ATTRIBUTE_MAP.items():
            if oidc_attr in access_info:
                info.setdefault(user_attr, access_info[oidc_attr])

        for oidc_attr, user_attr in settings.OIDC_ID_ATTRIBUTE_MAP.items():
            if oidc_attr in verified_id:
                info.setdefault(user_attr, verified_id[oidc_attr])

        return info

    def verify_access_token(
        self,
        access_token: str,
        verified_id: Mapping[str, object],
    ) -> dict[str, Any]:
        """Verify and bind a JWT access token to the authenticated identity."""
        try:
            if self.OIDC_RP_SIGN_ALGO.startswith(
                "RS"
            ) or self.OIDC_RP_SIGN_ALGO.startswith("ES"):
                if self.OIDC_RP_IDP_SIGN_KEY is not None:
                    key: Any = self.OIDC_RP_IDP_SIGN_KEY
                else:
                    key = self.retrieve_matching_jwk(access_token)
            else:
                key = self.OIDC_RP_CLIENT_SECRET

            claims = self._verify_jws(access_token, key)
        except (
            jwt.PyJWTError,
            requests.RequestException,
            SuspiciousOperation,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise SuspiciousOperation("OIDC access token verification failed.") from exc

        self.verify_access_token_claims(claims, verified_id)
        self.verify_access_token_hash(access_token, verified_id)

        return claims

    def verify_access_token_claims(
        self,
        claims: dict[str, Any],
        verified_id: Mapping[str, object],
    ) -> None:
        """Validate issuer, subject, lifetime, and client binding."""
        if not self.OIDC_OP_ISSUER:
            raise ImproperlyConfigured(
                "OIDC_OP_ISSUER must be configured to validate access tokens"
            )

        missing_claims = self.ACCESS_TOKEN_REQUIRED_CLAIMS.difference(claims)
        if missing_claims:
            missing = ", ".join(sorted(missing_claims))
            raise SuspiciousOperation(
                f"OIDC access token is missing required claims: {missing}"
            )

        if claims["iss"] != self.OIDC_OP_ISSUER:
            raise SuspiciousOperation("OIDC access token issuer does not match")

        id_subject = verified_id.get("sub")
        access_subject = claims["sub"]
        if (
            not isinstance(id_subject, str)
            or not id_subject
            or not isinstance(access_subject, str)
        ):
            raise SuspiciousOperation("OIDC token subject is invalid")

        if access_subject != id_subject:
            id_object = verified_id.get("oid")
            access_object = claims.get("oid")
            id_tenant = verified_id.get("tid")
            access_tenant = claims.get("tid")
            same_provider_object = (
                isinstance(id_object, str)
                and bool(id_object)
                and id_object == access_object
                and isinstance(id_tenant, str)
                and bool(id_tenant)
                and id_tenant == access_tenant
            )
            if not same_provider_object:
                raise SuspiciousOperation(
                    "OIDC access token subject does not match the ID token"
                )

        client_claim_names = ("azp", "client_id", "appid")
        client_claims = {
            claim_name: claims[claim_name]
            for claim_name in client_claim_names
            if claim_name in claims
        }
        if client_claims:
            if any(
                not isinstance(client_id, str) or client_id != self.OIDC_RP_CLIENT_ID
                for client_id in client_claims.values()
            ):
                raise SuspiciousOperation(
                    "OIDC access token client identifier does not match"
                )
            return

        audience_claim = claims.get("aud")
        if isinstance(audience_claim, str):
            audiences = [audience_claim]
        elif isinstance(audience_claim, list) and all(
            isinstance(audience, str) for audience in audience_claim
        ):
            audiences = audience_claim
        else:
            audiences = []

        if self.OIDC_RP_CLIENT_ID not in audiences:
            raise SuspiciousOperation("OIDC access token is not bound to this client")

    def verify_access_token_hash(
        self,
        access_token: str,
        verified_id: Mapping[str, object],
    ) -> None:
        """Validate the ID token's optional access-token hash."""
        expected_hash = verified_id.get("at_hash")
        if expected_hash is None:
            return
        if not isinstance(expected_hash, str) or not expected_hash:
            raise SuspiciousOperation("OIDC ID token access token hash is invalid")

        digest_name = {
            "256": "sha256",
            "384": "sha384",
            "512": "sha512",
        }.get(self.OIDC_RP_SIGN_ALGO[-3:])
        if digest_name is None:
            raise SuspiciousOperation("OIDC access token hash algorithm is unsupported")

        digest = hashlib.new(digest_name, access_token.encode()).digest()
        actual_hash = (
            base64.urlsafe_b64encode(digest[: len(digest) // 2]).rstrip(b"=").decode()
        )
        if not hmac.compare_digest(actual_hash, expected_hash):
            raise SuspiciousOperation("OIDC access token does not match the ID token")

    def create_user(self, user_info: dict[str, Any]) -> Optional[User]:
        role = self.get_user_role(user_info)
        if role is None:
            return None

        user = super().create_user(user_info)
        for attr, value in user_info.items():
            setattr(user, attr, value)
        self.set_user_role(user, role)
        generate_api_key(user)
        return user

    def update_user(self, user: User, user_info: dict[str, Any]) -> Optional[User]:
        """
        Updates the user's role only if the setting allows roles to be set from OIDC claims.
        If the setting is False roles are being managed by an admin so do not update the role.
        """
        if self.OIDC_OP_SET_ROLES_FROM_CLAIMS:
            role = self.get_user_role(user_info)
            if role is None:
                return None
            self.set_user_role(user, role)
        return user

    def set_user_role(self, user: User, role: str) -> None:
        """Assign a new role to a User given the role codename."""
        # Only users with the admin role are Django superusers.
        user.is_superuser = role == self.USER_ROLE_ADMIN
        user.save()

    def get_user_role(self, user_info: dict[str, Any]) -> Optional[str]:
        """
        Returns the highest-permission valid role found in the OIDC token claims.
        Returns the default user role if the setting is False.
        Returns None if no valid roles are found.
        """
        if not self.OIDC_OP_SET_ROLES_FROM_CLAIMS:
            return self.USER_ROLE_DEFAULT

        claim_path = self.OIDC_OP_ROLE_CLAIM_PATH.split(".")
        role_claims = user_info

        # Traverse the claim path to find the role claims.
        for key in claim_path:
            if isinstance(role_claims, dict):
                role_claims = role_claims.get(key, {})
            else:
                return None

        # If the claim contains a single role, convert to list.
        if isinstance(role_claims, str):
            role_claims = [role_claims]

        # Neither a string nor a list of roles.
        if not isinstance(role_claims, list):
            return None

        # The roles are ordered from highest to lowest permission in this list.
        # This feature is used in OIDC authentication to determine the highest
        # permission role of a user based on the claims received when multiple
        # roles are received.
        USER_ROLE_TO_ROLE_CLAIM_MAP = {
            self.USER_ROLE_ADMIN: self.OIDC_ROLE_CLAIM_ADMIN,
            self.USER_ROLE_DEFAULT: self.OIDC_ROLE_CLAIM_DEFAULT,
        }

        # Iterate over USER_ROLE_TO_ROLE_CLAIM_MAP and return the first matching role.
        for role_key, token_claim in USER_ROLE_TO_ROLE_CLAIM_MAP.items():
            if token_claim in role_claims:
                return role_key

        return None  # No match found.
