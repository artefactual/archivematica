from collections.abc import Sequence
from typing import IO
from typing import Protocol

SCOPE_BASE: int
SCOPE_ONELEVEL: int
SCOPE_SUBTREE: int
RES_SEARCH_ENTRY: int
RES_SEARCH_RESULT: int
VERSION3: int
OPT_PROTOCOL_VERSION: int
OPT_X_TLS_CACERTFILE: int
OPT_X_TLS_CERTFILE: int
OPT_X_TLS_KEYFILE: int
OPT_X_TLS_REQUIRE_CERT: int
OPT_X_TLS_NEVER: int
OPT_X_TLS_ALLOW: int
OPT_X_TLS_TRY: int
OPT_X_TLS_DEMAND: int
OPT_X_TLS_HARD: int

class LDAPError(Exception): ...
class INVALID_CREDENTIALS(LDAPError): ...
class NO_SUCH_OBJECT(LDAPError): ...
class DECODING_ERROR(LDAPError): ...
class INVALID_DN_SYNTAX(LDAPError): ...

_LDAPAttributeMap = dict[str, list[str]]
_LDAPSearchEntry = tuple[str, _LDAPAttributeMap]
_LDAPSearchResult = list[_LDAPSearchEntry]

class _LDAPObject(Protocol):
    def get_option(self, option: int) -> object: ...
    def set_option(self, option: int, invalue: object) -> None: ...
    def simple_bind_s(
        self,
        who: str = ...,
        cred: str = ...,
    ) -> tuple[int, list[object]]: ...
    def search(
        self,
        base: str,
        scope: int,
        filterstr: str = ...,
        attrlist: Sequence[str] | None = ...,
        attrsonly: int = ...,
    ) -> int: ...
    def result(
        self,
        msgid: int,
        all: int = ...,
        timeout: float | None = ...,
    ) -> tuple[int, _LDAPSearchResult]: ...
    def search_s(
        self,
        base: str,
        scope: int,
        filterstr: str = ...,
        attrlist: Sequence[str] | None = ...,
        attrsonly: int = ...,
    ) -> _LDAPSearchResult: ...
    def start_tls_s(self) -> None: ...
    def compare_s(self, dn: str, attr: str, value: str) -> int: ...
    def unbind(self) -> None: ...
    def unbind_s(self) -> None: ...

def initialize(
    uri: str,
    trace_level: int = ...,
    trace_file: IO[str] = ...,
    trace_stack_limit: int | None = ...,
    bytes_mode: bool | None = ...,
    fileno: int | None = ...,
    **kwargs: object,
) -> _LDAPObject: ...
def set_option(option: int, invalue: object) -> None: ...
