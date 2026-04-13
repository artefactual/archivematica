from collections.abc import Iterator
from collections.abc import Sequence
from typing import Literal

_BagTagValue = str | list[str]
_BagTags = dict[str, _BagTagValue]
_BagEntryChecksums = dict[str, str]
_BagEntries = dict[str, _BagEntryChecksums]

class BagError(Exception): ...

class BagValidationError(BagError):
    message: str
    details: list[object]

    def __init__(
        self,
        message: str,
        details: list[object] | None = ...,
    ) -> None: ...
    def __str__(self) -> str: ...

class Bag:
    tags: _BagTags
    info: _BagTags
    entries: _BagEntries
    normalized_filesystem_names: dict[str, str]
    normalized_manifest_names: dict[str, str]
    algorithms: list[str]
    tag_file_name: str | None
    path: str
    encoding: str
    version_info: tuple[int, int]

    def __init__(self, path: str) -> None: ...
    @property
    def algs(self) -> list[str]: ...
    @property
    def version(self) -> str: ...
    def manifest_files(self) -> Iterator[str]: ...
    def tagmanifest_files(self) -> Iterator[str]: ...
    def payload_entries(self) -> _BagEntries: ...
    def save(self, processes: int = ..., manifests: bool = ...) -> None: ...
    def fetch_entries(self) -> Iterator[tuple[str, str, str]]: ...
    def files_to_be_fetched(self) -> Iterator[str]: ...
    def validate(
        self,
        processes: int = ...,
        fast: bool = ...,
        completeness_only: bool = ...,
    ) -> Literal[True]: ...
    def is_valid(
        self,
        processes: int = ...,
        fast: bool = ...,
        completeness_only: bool = ...,
    ) -> bool: ...

def make_bag(
    bag_dir: str,
    bag_info: dict[str, _BagTagValue] | None = ...,
    processes: int = ...,
    checksums: Sequence[str] | None = ...,
    checksum: Sequence[str] | None = ...,
    encoding: str = ...,
) -> Bag: ...
