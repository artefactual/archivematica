# mypy: disable-error-code=override

from collections.abc import Mapping

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User
from django.http import HttpRequest

class ShibbolethRemoteUserBackend(RemoteUserBackend):
    def __init__(self) -> None: ...
    def authenticate(
        self,
        request: HttpRequest | None,
        remote_user: str | None,
        shib_meta: Mapping[str, object],
    ) -> User | None: ...
    def setup_user(
        self,
        request: HttpRequest | None,
        username: str,
        defaults: Mapping[str, object],
    ) -> User | None: ...
    def handle_created_user(
        self,
        request: HttpRequest | None,
        user: User,
    ) -> User: ...
    @staticmethod
    def update_user_params(user: User, params: Mapping[str, object]) -> None: ...
