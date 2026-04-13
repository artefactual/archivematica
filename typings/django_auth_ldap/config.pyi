from collections.abc import Mapping
from collections.abc import Sequence

from ldap import _LDAPObject
from ldap import _LDAPSearchResult

class LDAPSearch:
    def __init__(
        self,
        base_dn: str | None,
        scope: int,
        filterstr: str = ...,
        attrlist: Sequence[str] | None = ...,
    ) -> None: ...
    def search_with_additional_terms(
        self,
        term_dict: Mapping[str, str],
        escape: bool = ...,
    ) -> LDAPSearch: ...
    def search_with_additional_term_string(self, filterstr: str) -> LDAPSearch: ...
    def execute(
        self,
        connection: _LDAPObject,
        filterargs: tuple[object, ...] | Mapping[str, object] = ...,
        escape: bool = ...,
    ) -> _LDAPSearchResult: ...

class ActiveDirectoryGroupType:
    def __init__(self, name_attr: str = ...) -> None: ...
