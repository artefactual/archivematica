from django.contrib.auth.models import User
from django.dispatch import Signal
from django.http import HttpRequest

class LDAPBackend:
    def __init__(self) -> None: ...
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = ...,
        password: str | None = ...,
        **kwargs: object,
    ) -> User | None: ...
    def ldap_to_django_username(self, username: str) -> str: ...
    def django_to_ldap_username(self, username: str) -> str: ...
    def populate_user(self, username: str) -> User | None: ...

populate_user: Signal
ldap_error: Signal
