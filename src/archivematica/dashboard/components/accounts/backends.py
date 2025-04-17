import json
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django_auth_ldap.backend import LDAPBackend
from django_cas_ng.backends import CASBackend
from josepy.jws import JWS
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Store additional settings as instance attributes.
        self.OIDC_OP_SET_ROLES_FROM_CLAIMS = getattr(
            settings, "OIDC_OP_SET_ROLES_FROM_CLAIMS", False
        )
        self.OIDC_OP_ROLE_CLAIM_PATH = getattr(
            settings, "OIDC_OP_ROLE_CLAIM_PATH", "realm_access.roles"
        )

        self.USER_ROLE_ADMIN = getattr(settings, "USER_ROLE_ADMIN", "admin")

    def get_settings(self, attr: str, *args: Any) -> Any:
        if attr in [
            "OIDC_RP_CLIENT_ID",
            "OIDC_RP_CLIENT_SECRET",
            "OIDC_OP_AUTHORIZATION_ENDPOINT",
            "OIDC_OP_TOKEN_ENDPOINT",
            "OIDC_OP_USER_ENDPOINT",
            "OIDC_OP_JWKS_ENDPOINT",
            "OIDC_OP_LOGOUT_ENDPOINT",
            "OIDC_OP_SET_ROLES_FROM_CLAIMS",
            "OIDC_OP_ROLE_CLAIM_PATH",
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
        self.OIDC_OP_SET_ROLES_FROM_CLAIMS = self.get_settings(
            "OIDC_OP_SET_ROLES_FROM_CLAIMS"
        )
        self.OIDC_OP_ROLE_CLAIM_PATH = self.get_settings("OIDC_OP_ROLE_CLAIM_PATH")

        return super().authenticate(request, **kwargs)

    def get_userinfo(self, access_token, id_token, verified_id):
        """
        Extract user details from JSON web tokens
        These map to fields on the user field.
        """

        def decode_token(token):
            sig = JWS.from_compact(token.encode("utf-8"))
            payload = sig.payload.decode("utf-8")
            return json.loads(payload)

        access_info = decode_token(access_token)
        id_info = decode_token(id_token)

        info = {}

        for oidc_attr, user_attr in settings.OIDC_ACCESS_ATTRIBUTE_MAP.items():
            if oidc_attr in access_info:
                info.setdefault(user_attr, access_info[oidc_attr])

        for oidc_attr, user_attr in settings.OIDC_ID_ATTRIBUTE_MAP.items():
            if oidc_attr in id_info:
                info.setdefault(user_attr, id_info[oidc_attr])

        return info

    def create_user(self, user_info: dict[str, Any]) -> User:
        user = super().create_user(user_info)
        for attr, value in user_info.items():
            setattr(user, attr, value)
        user.save()
        self.set_user_role(user, user_info)
        generate_api_key(user)
        return user

    def update_user(self, user: User, user_info: dict[str, Any]) -> User:
        """Updates the user's role only if the setting allows roles to be set from OIDC claims."""
        if self.OIDC_OP_SET_ROLES_FROM_CLAIMS:
            self.set_user_role(user, user_info)
        return user

    def set_user_role(self, user: User, user_info: dict[str, Any]) -> None:
        """
        Assigns the user's role based on OIDC token claims if enabled in settings.
        Otherwise, assigns the default role.
        """
        if self.OIDC_OP_SET_ROLES_FROM_CLAIMS:
            # Get the role claim path from settings (e.g. "realm_access.roles").
            claim_path = self.OIDC_OP_ROLE_CLAIM_PATH.split(".")  # Convert to a list

            role = user_info
            for key in claim_path:
                if isinstance(role, dict):
                    role = role.get(key, {})
                else:
                    role = {}
                    break

            # If role is a list, pick the first one.
            if isinstance(role, list) and role:
                role = role[0]

            is_superuser = False
            if role and role in self.USER_ROLE_ADMIN:
                is_superuser = True

            if user.is_superuser != is_superuser:
                user.is_superuser = is_superuser
                user.save()
