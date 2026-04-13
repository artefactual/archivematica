from django.contrib.auth.models import User
from django.http import HttpRequest

from .http import HttpUnauthorized

class Authentication:
    auth_type: str
    require_active: bool

    def __init__(self, require_active: bool = ...) -> None: ...
    def get_authorization_data(self, request: HttpRequest) -> str: ...
    def is_authenticated(
        self,
        request: HttpRequest,
        **kwargs: object,
    ) -> bool | HttpUnauthorized: ...
    def get_identifier(self, request: HttpRequest) -> str: ...
    def check_active(self, user: User) -> bool: ...

class BasicAuthentication(Authentication):
    backend: object | None
    realm: str

    def __init__(
        self,
        backend: object | None = ...,
        realm: str = ...,
        **kwargs: object,
    ) -> None: ...
    def extract_credentials(self, request: HttpRequest) -> tuple[str, str]: ...
    def is_authenticated(
        self,
        request: HttpRequest,
        **kwargs: object,
    ) -> bool | HttpUnauthorized: ...

class ApiKeyAuthentication(Authentication):
    def extract_credentials(
        self, request: HttpRequest
    ) -> tuple[str | None, str | None]: ...
    def is_authenticated(
        self,
        request: HttpRequest,
        **kwargs: object,
    ) -> bool | HttpUnauthorized: ...
    def get_key(self, user: User, api_key: str) -> bool | HttpUnauthorized: ...

class SessionAuthentication(Authentication):
    def is_authenticated(
        self,
        request: HttpRequest,
        **kwargs: object,
    ) -> bool | HttpUnauthorized: ...

class MultiAuthentication:
    backends: tuple[Authentication, ...]

    def __init__(self, *backends: Authentication) -> None: ...
    def is_authenticated(
        self,
        request: HttpRequest,
        **kwargs: object,
    ) -> bool | HttpUnauthorized: ...
    def get_identifier(self, request: HttpRequest) -> str: ...
