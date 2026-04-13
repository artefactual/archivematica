_Note = dict[str, str]
_Record = dict[str, object]
_CollectionRecord = dict[str, object]

class ArchivesSpaceError(Exception): ...
class ConnectionError(ArchivesSpaceError): ...
class AuthenticationError(ArchivesSpaceError): ...

class ArchivesSpaceClient:
    RESOURCE: str
    RESOURCE_COMPONENT: str

    def __init__(
        self,
        host: str,
        user: str,
        passwd: str,
        port: int = ...,
        repository: int = ...,
        timeout: int = ...,
    ) -> None: ...
    def logout(self) -> None: ...
    def get_record(self, record_id: str) -> _Record: ...
    def edit_record(self, new_record: _Record) -> None: ...
    def find_parent_id_for_component(self, component_id: str) -> tuple[str, str]: ...
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
    def add_digital_object(
        self,
        parent_archival_object: str,
        identifier: str,
        title: str | None = ...,
        uri: str | None = ...,
        location_of_originals: str | None = ...,
        object_type: str = ...,
        xlink_show: str = ...,
        xlink_actuate: str = ...,
        restricted: bool = ...,
        use_statement: str = ...,
        use_conditions: str | None = ...,
        access_conditions: str | None = ...,
        size: int | None = ...,
        format_name: str | None = ...,
        format_version: str | None = ...,
        inherit_dates: bool = ...,
        inherit_notes: bool = ...,
    ) -> _Record: ...
    def add_child(
        self,
        parent: str,
        title: str = ...,
        level: str = ...,
        start_date: str = ...,
        end_date: str = ...,
        date_expression: str = ...,
        notes: list[_Note] | None = ...,
    ) -> str: ...
