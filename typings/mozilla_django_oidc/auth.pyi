# mypy: disable-error-code=override

from collections.abc import Mapping
from collections.abc import Sequence

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.http import HttpRequest

_OIDCClaims = Mapping[str, object]

def default_username_algo(
    email: str | None,
    claims: _OIDCClaims | None = ...,
) -> str: ...

class OIDCAuthenticationBackend(ModelBackend):
    OIDC_OP_TOKEN_ENDPOINT: str
    OIDC_OP_USER_ENDPOINT: str
    OIDC_OP_JWKS_ENDPOINT: str | None
    OIDC_RP_CLIENT_ID: str
    OIDC_RP_CLIENT_SECRET: str
    OIDC_RP_SIGN_ALGO: str
    OIDC_RP_IDP_SIGN_KEY: str | None
    UserModel: type[User]

    def __init__(self, *args: object, **kwargs: object) -> None: ...
    @staticmethod
    def get_settings(attr: str, *args: object) -> object: ...
    def describe_user_by_claims(self, claims: _OIDCClaims) -> str: ...
    def filter_users_by_claims(self, claims: _OIDCClaims) -> Sequence[User]: ...
    def verify_claims(self, claims: _OIDCClaims) -> bool: ...
    def create_user(self, claims: _OIDCClaims) -> User: ...
    def get_username(self, claims: _OIDCClaims) -> str: ...
    def update_user(self, user: User, claims: _OIDCClaims) -> User: ...
    def get_userinfo(
        self,
        access_token: str,
        id_token: str,
        payload: _OIDCClaims | None,
    ) -> dict[str, object]: ...
    def authenticate(
        self,
        request: HttpRequest | None,
        **kwargs: object,
    ) -> User | None: ...
