from requests import Response

_Note = dict[str, str]
_Record = dict[str, object]
_CollectionRecord = dict[str, object]

class AtomError(Exception): ...
class ConnectionError(AtomError): ...
class AuthenticationError(AtomError): ...

class CommunicationError(AtomError):
    response: Response

    def __init__(self, status_code: int, response: Response) -> None: ...

class AtomClient:
    def __init__(self, url: str, key: str, timeout: int = ...) -> None: ...
    def get_record(self, record_id: str) -> _Record: ...
    def edit_record(self, new_record: _Record) -> None: ...
    def find_parent_id_for_component(self, slug: str) -> str: ...
    def count_collections(
        self,
        search_pattern: str = ...,
        identifier: str = ...,
    ) -> int: ...
    def find_collections(
        self,
        search_pattern: str = ...,
        identifier: str = ...,
        fetched: int = ...,
        page: int = ...,
        page_size: int = ...,
        sort_by: str | None = ...,
    ) -> list[_CollectionRecord]: ...
    def add_child(
        self,
        parent_slug: str | None = ...,
        title: str = ...,
        level: str = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
        date_expression: str | None = ...,
        notes: list[_Note] | None = ...,
    ) -> str: ...
    def add_digital_object(
        self,
        information_object_slug: str,
        identifier: str | None = ...,
        title: str | None = ...,
        uri: str | None = ...,
        location_of_originals: str | None = ...,
        object_type: str | None = ...,
        xlink_show: str = ...,
        xlink_actuate: str = ...,
        restricted: bool = ...,
        use_statement: str = ...,
        use_conditions: str | None = ...,
        access_conditions: str | None = ...,
        size: int | None = ...,
        format_name: str | None = ...,
        format_version: str | None = ...,
        format_registry_key: str | None = ...,
        format_registry_name: str | None = ...,
        file_uuid: str | None = ...,
        aip_uuid: str | None = ...,
        inherit_dates: bool = ...,
        usage: str | None = ...,
        aip_name: str | None = ...,
        relative_path_within_aip: str | None = ...,
    ) -> _Record: ...
